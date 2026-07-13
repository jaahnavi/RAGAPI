"""
API endpoint tests.

Uses an in-memory SQLite database (StaticPool so all sessions share one
connection) via FastAPI dependency override. Heavy operations — PDF parsing,
embeddings, LLM — are mocked so no external services are required.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.document import Documents
from main import app

# ── test database ─────────────────────────────────────────────────────────────

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_test_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    """Recreate all tables before each test and drop them after."""
    Base.metadata.create_all(_test_engine)
    yield
    Base.metadata.drop_all(_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def inserted_doc():
    """Insert a completed document into the test DB and yield it detached."""
    db = _TestSession()
    doc = Documents(
        uuid="aaaabbbb-cccc-dddd-eeee-ffffffffffff",
        filename="uploaded.pdf",
        filepath="data/uploads/uploaded.pdf",
        content_hash="a" * 64,
        status="done",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.expunge(doc)   # detach so the session can be released safely
    db.close()
    yield doc


def _fake_doc(status="done"):
    """Return an unsaved Documents instance suitable for use in mocks."""
    return Documents(
        id=1,
        uuid="fake-uuid-0001",
        filename="sample.pdf",
        filepath="data/uploads/sample.pdf",
        content_hash="b" * 64,
        status=status,
        error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── POST /documents/ — file upload ────────────────────────────────────────────

@patch("app.api.documents.run_pipeline")
@patch("app.api.documents.save_uploaded_pdf", new_callable=AsyncMock)
def test_upload_pdf_success(mock_save, mock_pipeline, client):
    mock_save.return_value = (_fake_doc(), True)

    resp = client.post(
        "/documents/",
        files={"file": ("report.pdf", b"%PDF-1.4 minimal", "application/pdf")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["already_exists"] is False
    mock_pipeline.assert_called_once()


@patch("app.api.documents.save_uploaded_pdf", new_callable=AsyncMock)
def test_upload_non_pdf_returns_400(mock_save, client):
    mock_save.side_effect = Exception("Only PDF files are accepted")

    resp = client.post(
        "/documents/",
        files={"file": ("notes.docx", b"not-a-pdf", "application/octet-stream")},
    )

    assert resp.status_code == 400
    assert "PDF" in resp.json()["detail"]


@patch("app.api.documents.run_pipeline")
@patch("app.api.documents.save_uploaded_pdf", new_callable=AsyncMock)
def test_upload_duplicate_pdf_returns_already_exists(mock_save, mock_pipeline, client):
    mock_save.return_value = (_fake_doc(), False)  # is_new=False

    resp = client.post(
        "/documents/",
        files={"file": ("report.pdf", b"%PDF-1.4 duplicate", "application/pdf")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["already_exists"] is True
    mock_pipeline.assert_not_called()


# ── POST /documents/upload-url ────────────────────────────────────────────────

@patch("app.api.documents.run_pipeline")
@patch("app.api.documents.download_pdf")
def test_upload_url_success(mock_download, mock_pipeline, client):
    mock_download.return_value = (_fake_doc(), True)

    resp = client.post(
        "/documents/upload-url",
        json={"url": "https://www.medicare.gov/publications/handbook.pdf"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["already_exists"] is False
    mock_pipeline.assert_called_once()


@patch("app.api.documents.run_pipeline")
@patch("app.api.documents.download_pdf")
def test_upload_url_duplicate_skips_pipeline(mock_download, mock_pipeline, client):
    mock_download.return_value = (_fake_doc(), False)

    resp = client.post(
        "/documents/upload-url",
        json={"url": "https://www.medicare.gov/publications/handbook.pdf"},
    )

    assert resp.status_code == 200
    assert resp.json()["already_exists"] is True
    mock_pipeline.assert_not_called()


# ── GET /documents/ ───────────────────────────────────────────────────────────

def test_list_documents_empty(client):
    resp = client.get("/documents/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["documents"] == []


def test_list_documents_returns_inserted_doc(client, inserted_doc):
    resp = client.get("/documents/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    doc = body["documents"][0]
    assert doc["filename"] == "uploaded.pdf"
    assert doc["status"] == "done"


# ── DELETE /documents/{id} ────────────────────────────────────────────────────

@patch("app.api.documents.os.path.exists", return_value=False)
@patch("app.api.documents.Chroma")
def test_delete_document_success(mock_chroma, mock_path_exists, client, inserted_doc):
    mock_chroma.return_value = MagicMock()

    resp = client.delete(f"/documents/{inserted_doc.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["deleted_id"] == inserted_doc.id

    # confirm it no longer appears in the list
    assert client.get("/documents/").json()["total"] == 0


def test_delete_nonexistent_document_returns_404(client):
    resp = client.delete("/documents/9999")

    assert resp.status_code == 404


# ── POST /chat/ ───────────────────────────────────────────────────────────────

@patch("app.api.chat.ask")
def test_chat_returns_answer_and_sources(mock_ask, client):
    mock_ask.return_value = {
        "answer": "Medicare Part A covers inpatient hospital stays.",
        "sources": [
            {"content": "Part A covers hospital...", "metadata": {"source": "handbook.pdf", "page": 5}},
        ],
    }

    resp = client.post("/chat/", json={"message": "What does Medicare Part A cover?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "Medicare Part A covers inpatient hospital stays."
    assert len(body["sources"]) == 1
    assert body["sources"][0]["content"] == "Part A covers hospital..."


@patch("app.api.chat.ask")
def test_chat_passes_custom_k_and_alpha_to_pipeline(mock_ask, client):
    mock_ask.return_value = {"answer": "ok", "sources": []}

    client.post("/chat/", json={"message": "test question", "k": 3, "alpha": 0.7})

    mock_ask.assert_called_once_with("test question", k=3, alpha=0.7)


@patch("app.api.chat.ask")
def test_chat_uses_default_k_and_alpha(mock_ask, client):
    mock_ask.return_value = {"answer": "ok", "sources": []}

    client.post("/chat/", json={"message": "hello"})

    mock_ask.assert_called_once_with("hello", k=5, alpha=0.5)
