from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.rag.retriever import hybrid_search


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_vs(texts: list[str], ids: list[str], vector_hits: list[tuple[Document, float]]):
    """Return a mock vectorstore with a pre-loaded corpus and vector hits."""
    mock_vs = MagicMock()
    mock_vs.get.return_value = {
        "documents": texts,
        "metadatas": [{"source": f"file_{i}.pdf", "page": i} for i in range(len(texts))],
        "ids": ids,
    }
    mock_vs.similarity_search_with_relevance_scores.return_value = vector_hits
    return mock_vs


def _doc(text: str, source: str = "test.pdf") -> Document:
    return Document(page_content=text, metadata={"source": source})


# ---------------------------------------------------------------------------
# shared corpus
# ---------------------------------------------------------------------------

CORPUS_TEXTS = [
    "deductible is the amount you pay before insurance kicks in",   # id_0
    "copay is a fixed fee paid at each doctor visit",               # id_1
    "network providers are doctors covered by your plan",           # id_2
    "out of pocket maximum limits your total yearly spending",      # id_3
    "premium is the monthly cost of your health insurance plan",    # id_4
]
CORPUS_IDS = [f"id_{i}" for i in range(len(CORPUS_TEXTS))]


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

@patch("app.rag.retriever._get_vectorstore")
def test_returns_at_most_k_results(mock_get_vs):
    vector_hits = [(_doc(CORPUS_TEXTS[i]), 0.9 - i * 0.1) for i in range(5)]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    results = hybrid_search("deductible copay", k=3)

    assert len(results) <= 3


@patch("app.rag.retriever._get_vectorstore")
def test_returns_document_objects(mock_get_vs):
    vector_hits = [(_doc(CORPUS_TEXTS[0]), 0.9)]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    results = hybrid_search("deductible", k=5)

    assert all(isinstance(r, Document) for r in results)


@patch("app.rag.retriever._get_vectorstore")
def test_empty_corpus_returns_empty_list(mock_get_vs):
    mock_vs = MagicMock()
    mock_vs.get.return_value = {"documents": [], "metadatas": [], "ids": []}
    mock_vs.similarity_search_with_relevance_scores.return_value = []
    mock_get_vs.return_value = mock_vs

    results = hybrid_search("anything", k=5)

    assert results == []


@patch("app.rag.retriever._get_vectorstore")
def test_deduplication_doc_appears_once(mock_get_vs):
    """A chunk that ranks in both vector and BM25 lists must appear only once."""
    vector_hits = [
        (_doc(CORPUS_TEXTS[0]), 0.95),
        (_doc(CORPUS_TEXTS[1]), 0.70),
    ]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    results = hybrid_search("deductible", k=5)
    contents = [r.page_content for r in results]

    assert contents.count(CORPUS_TEXTS[0]) == 1


@patch("app.rag.retriever._get_vectorstore")
def test_alpha_1_pure_vector_preserves_vector_rank(mock_get_vs):
    """With alpha=1.0 BM25 contributes zero; output order must follow vector rank."""
    vector_hits = [
        (_doc(CORPUS_TEXTS[3]), 0.99),
        (_doc(CORPUS_TEXTS[1]), 0.85),
        (_doc(CORPUS_TEXTS[0]), 0.70),
    ]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    results = hybrid_search("out of pocket", k=3, alpha=1.0)

    assert results[0].page_content == CORPUS_TEXTS[3]
    assert results[1].page_content == CORPUS_TEXTS[1]


@patch("app.rag.retriever._get_vectorstore")
def test_alpha_0_bm25_surfaces_doc_missed_by_vector(mock_get_vs):
    """With alpha=0.0 vector contributes zero; BM25 can surface docs vector missed."""
    # Vector returns chunks that do NOT contain "deductible"
    vector_hits = [
        (_doc(CORPUS_TEXTS[2]), 0.80),
        (_doc(CORPUS_TEXTS[4]), 0.75),
    ]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    # id_0 is the only chunk with "deductible" — BM25 must rank it first
    results = hybrid_search("deductible", k=1, alpha=0.0)

    assert results[0].page_content == CORPUS_TEXTS[0]


@patch("app.rag.retriever._get_vectorstore")
def test_score_threshold_excludes_low_vector_scores(mock_get_vs):
    """Docs below score_threshold are excluded from vector side (alpha=1.0 so no BM25 rescue)."""
    vector_hits = [
        (_doc(CORPUS_TEXTS[0]), 0.85),
        (_doc(CORPUS_TEXTS[1]), 0.20),   # below threshold=0.5
    ]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    results = hybrid_search("deductible", k=5, alpha=1.0, score_threshold=0.5)
    contents = [r.page_content for r in results]

    assert CORPUS_TEXTS[1] not in contents


@patch("app.rag.retriever._get_vectorstore")
def test_hybrid_combines_both_signals(mock_get_vs):
    """A doc absent from vector results but present in BM25 should appear when alpha<1."""
    # Vector misses id_0 (the "deductible" chunk)
    vector_hits = [
        (_doc(CORPUS_TEXTS[2]), 0.90),
        (_doc(CORPUS_TEXTS[3]), 0.80),
    ]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    results = hybrid_search("deductible", k=5, alpha=0.5)
    contents = [r.page_content for r in results]

    assert CORPUS_TEXTS[0] in contents


@patch("app.rag.retriever._get_vectorstore")
def test_k_caps_output_length(mock_get_vs):
    """Final output is always capped at k regardless of fetch_k."""
    vector_hits = [(_doc(CORPUS_TEXTS[i]), 0.9 - i * 0.05) for i in range(5)]
    mock_get_vs.return_value = _make_vs(CORPUS_TEXTS, CORPUS_IDS, vector_hits)

    for k in (1, 2, 4):
        results = hybrid_search("plan", k=k, fetch_k=10)
        assert len(results) <= k
