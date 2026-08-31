from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.rag.retriever import hybrid_search


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _hit(content: str, score: float, doc_id="doc-1", filename="test.pdf", page=0, chunk_index=0):
    """A dict shaped like one row from SearchClient.search() — Azure's SDK
    returns dict-like results with the fused/BM25/vector score under
    '@search.score' alongside the selected fields."""
    return {
        "id": f"{doc_id}-{chunk_index}",
        "content": content,
        "doc_id": doc_id,
        "filename": filename,
        "source": filename,
        "source_type": "upload",
        "page": page,
        "chunk_index": chunk_index,
        "@search.score": score,
    }


def _mock_client(hits: list[dict]) -> MagicMock:
    client = MagicMock()
    client.search.return_value = hits
    return client


CORPUS_TEXTS = [
    "deductible is the amount you pay before insurance kicks in",
    "copay is a fixed fee paid at each doctor visit",
    "network providers are doctors covered by your plan",
    "out of pocket maximum limits your total yearly spending",
    "premium is the monthly cost of your health insurance plan",
]


# ---------------------------------------------------------------------------
# response shaping
# ---------------------------------------------------------------------------

@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_returns_document_objects(mock_embeddings, mock_get_client):
    mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_get_client.return_value = _mock_client([_hit(CORPUS_TEXTS[0], 0.9)])

    results = hybrid_search("deductible", k=5)

    assert all(isinstance(r, Document) for r in results)
    assert results[0].page_content == CORPUS_TEXTS[0]
    assert results[0].metadata["filename"] == "test.pdf"


@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_empty_results_returns_empty_list(mock_embeddings, mock_get_client):
    mock_embeddings.embed_query.return_value = [0.1]
    mock_get_client.return_value = _mock_client([])

    results = hybrid_search("anything", k=5)

    assert results == []


@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_k_caps_output_length(mock_embeddings, mock_get_client):
    mock_embeddings.embed_query.return_value = [0.1]
    hits = [_hit(f"chunk {i}", 0.9 - i * 0.05, chunk_index=i) for i in range(5)]
    mock_get_client.return_value = _mock_client(hits)

    for k in (1, 2, 4):
        results = hybrid_search("plan", k=k, fetch_k=10)
        assert len(results) <= k


@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_score_threshold_excludes_low_scores(mock_embeddings, mock_get_client):
    mock_embeddings.embed_query.return_value = [0.1]
    hits = [
        _hit("high score chunk", 0.85, chunk_index=0),
        _hit("low score chunk", 0.20, chunk_index=1),
    ]
    mock_get_client.return_value = _mock_client(hits)

    results = hybrid_search("deductible", k=5, alpha=1.0, score_threshold=0.5)
    contents = [r.page_content for r in results]

    assert "low score chunk" not in contents
    assert "high score chunk" in contents


def test_confidence_threshold_guard_returns_empty(monkeypatch):
    monkeypatch.setattr("app.rag.retriever.settings.confidence_threshold", 0.5)
    with patch("app.rag.retriever.embeddings") as mock_embeddings, \
         patch("app.rag.retriever.get_search_client") as mock_get_client:
        mock_embeddings.embed_query.return_value = [0.1]
        mock_get_client.return_value = _mock_client([_hit("weak match", 0.1)])

        results = hybrid_search("unrelated", k=5, alpha=1.0)

    assert results == []


# ---------------------------------------------------------------------------
# alpha -> query construction (vector-only / keyword-only / hybrid)
# ---------------------------------------------------------------------------

@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_alpha_1_is_vector_only(mock_embeddings, mock_get_client):
    mock_embeddings.embed_query.return_value = [0.1, 0.2]
    client = _mock_client([_hit(CORPUS_TEXTS[0], 0.9)])
    mock_get_client.return_value = client

    hybrid_search("out of pocket", alpha=1.0)

    _, kwargs = client.search.call_args
    assert kwargs["search_text"] is None
    assert kwargs["vector_queries"] is not None
    mock_embeddings.embed_query.assert_called_once()


@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_alpha_0_is_keyword_only(mock_embeddings, mock_get_client):
    client = _mock_client([_hit(CORPUS_TEXTS[0], 0.9)])
    mock_get_client.return_value = client

    hybrid_search("deductible", alpha=0.0)

    _, kwargs = client.search.call_args
    assert kwargs["search_text"] == "deductible"
    assert kwargs["vector_queries"] is None
    mock_embeddings.embed_query.assert_not_called()


@patch("app.rag.retriever.get_search_client")
@patch("app.rag.retriever.embeddings")
def test_alpha_between_uses_hybrid(mock_embeddings, mock_get_client):
    mock_embeddings.embed_query.return_value = [0.1]
    client = _mock_client([_hit(CORPUS_TEXTS[0], 0.9)])
    mock_get_client.return_value = client

    hybrid_search("deductible", alpha=0.5)

    _, kwargs = client.search.call_args
    assert kwargs["search_text"] == "deductible"
    assert kwargs["vector_queries"] is not None
