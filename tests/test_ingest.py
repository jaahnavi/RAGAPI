"""
Unit tests for the ingestion layer: parser, chunker, and table formatter.

pdfplumber and PyPDFLoader are mocked so no real PDF files or external
services are needed.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.ingest.chunker import chunk_text
from app.ingest.parser import _table_to_markdown, extract_text_from_pdf


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_page(text: str, tables=None):
    """
    Build a mock pdfplumber page.

    When tables is provided (list of raw table data), find_tables() and
    extract_tables() are configured accordingly. outside_bbox() returns a
    cropped mock whose extract_text() yields the same text.
    """
    tables = tables or []
    page = MagicMock()
    page.find_tables.return_value = [MagicMock(bbox=(0, 0, 200, 50)) for _ in tables]
    page.extract_tables.return_value = tables
    page.extract_text.return_value = text

    cropped = MagicMock()
    cropped.extract_text.return_value = text
    page.outside_bbox.return_value = cropped

    return page


def _pdf_context(pages):
    """Return a mock context manager for pdfplumber.open() with the given pages."""
    ctx = MagicMock()
    ctx.pages = pages
    cm = MagicMock()
    cm.__enter__.return_value = ctx
    cm.__exit__.return_value = False
    return cm


# ── extract_text_from_pdf ─────────────────────────────────────────────────────

@patch("app.ingest.parser.pdfplumber")
def test_extract_returns_list_of_documents(mock_pdfplumber):
    mock_pdfplumber.open.return_value = _pdf_context([
        _mock_page("First page content"),
        _mock_page("Second page content"),
    ])

    result = extract_text_from_pdf(Path("any.pdf"))

    assert isinstance(result, list)
    assert all(isinstance(doc, Document) for doc in result)


@patch("app.ingest.parser.pdfplumber")
def test_extract_returns_one_document_per_page(mock_pdfplumber):
    mock_pdfplumber.open.return_value = _pdf_context([_mock_page(f"Page {i}") for i in range(4)])

    result = extract_text_from_pdf(Path("any.pdf"))

    assert len(result) == 4


@patch("app.ingest.parser.pdfplumber")
def test_extract_sets_source_and_page_in_metadata(mock_pdfplumber):
    mock_pdfplumber.open.return_value = _pdf_context([_mock_page("some text")])

    result = extract_text_from_pdf(Path("data/seed/handbook.pdf"))

    assert result[0].metadata["source"] == str(Path("data/seed/handbook.pdf"))
    assert result[0].metadata["page"] == 0


@patch("app.ingest.parser.pdfplumber")
def test_extract_table_rendered_as_markdown_in_page_content(mock_pdfplumber):
    table = [["Plan", "Deductible"], ["Gold", "$500"]]
    mock_pdfplumber.open.return_value = _pdf_context([_mock_page("body text", tables=[table])])

    result = extract_text_from_pdf(Path("any.pdf"))

    assert "Plan" in result[0].page_content
    assert "Deductible" in result[0].page_content
    assert "$500" in result[0].page_content


@patch("app.ingest.parser.pdfplumber")
def test_extract_falls_back_to_pypdf_on_pdfplumber_error(mock_pdfplumber):
    mock_pdfplumber.open.side_effect = Exception("corrupted PDF")

    fallback = Document(page_content="fallback text", metadata={"source": "any.pdf", "page": 0})
    with patch("app.ingest.parser.PyPDFLoader") as mock_loader:
        mock_loader.return_value.load.return_value = [fallback]
        result = extract_text_from_pdf(Path("any.pdf"))

    assert result[0].page_content == "fallback text"


# ── chunk_text ────────────────────────────────────────────────────────────────

def test_chunk_text_returns_document_objects():
    pages = [Document(page_content="word " * 300, metadata={"source": "t.pdf", "page": 0})]

    chunks = chunk_text(pages)

    assert all(isinstance(c, Document) for c in chunks)


def test_chunk_text_splits_long_text_into_multiple_chunks():
    pages = [Document(page_content="word " * 500, metadata={"source": "t.pdf", "page": 0})]

    chunks = chunk_text(pages, chunk_size=100, overlap=10)

    assert len(chunks) > 1


def test_chunk_text_leaves_short_text_as_single_chunk():
    pages = [Document(page_content="Short sentence.", metadata={"source": "t.pdf", "page": 0})]

    chunks = chunk_text(pages, chunk_size=512)

    assert len(chunks) == 1
    assert chunks[0].page_content == "Short sentence."


def test_chunk_text_preserves_all_metadata_fields():
    meta = {"source": "handbook.pdf", "page": 7, "doc_id": 42}
    pages = [Document(page_content="word " * 200, metadata=meta)]

    chunks = chunk_text(pages)

    for chunk in chunks:
        assert chunk.metadata["source"] == "handbook.pdf"
        assert chunk.metadata["page"] == 7
        assert chunk.metadata["doc_id"] == 42


def test_chunk_size_limits_chunk_length():
    pages = [Document(page_content="word " * 500, metadata={"source": "t.pdf", "page": 0})]
    chunk_size = 200

    chunks = chunk_text(pages, chunk_size=chunk_size)

    # allow 2× tolerance for splitter boundary detection
    for chunk in chunks:
        assert len(chunk.page_content) <= chunk_size * 2


# ── _table_to_markdown ────────────────────────────────────────────────────────

def test_table_to_markdown_empty_table_returns_empty_string():
    assert _table_to_markdown([]) == ""


def test_table_to_markdown_inserts_header_separator():
    result = _table_to_markdown([["Name", "Value"], ["Alice", "100"]])

    lines = result.split("\n")
    assert "---" in lines[1]   # separator is second line


def test_table_to_markdown_single_row_still_has_separator():
    result = _table_to_markdown([["ColA", "ColB"]])

    lines = result.split("\n")
    assert len(lines) >= 2
    assert "---" in lines[1]


def test_table_to_markdown_multi_row_preserves_all_data():
    table = [["Header1", "Header2"], ["R1C1", "R1C2"], ["R2C1", "R2C2"]]

    result = _table_to_markdown(table)

    assert "Header1" in result
    assert "R1C1" in result
    assert "R2C2" in result


def test_table_to_markdown_none_cells_do_not_crash():
    table = [["Name", None], [None, "value"]]

    result = _table_to_markdown(table)

    assert isinstance(result, str)
    assert "Name" in result
