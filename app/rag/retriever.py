from __future__ import annotations

from typing import List

from azure.search.documents.models import VectorizedQuery
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.store.vector_store import get_search_client

embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.azure_openai_embedding_api_key or "not-set",
    base_url=settings.azure_openai_embedding_endpoint,
)

_SELECT_FIELDS = ["id", "content", "doc_id", "filename", "source", "source_type", "page", "chunk_index"]


def hybrid_search(
    query: str,
    k: int = 10,
    fetch_k: int = 20,
    alpha: float = 0.5,
    score_threshold: float = settings.score_threshold,
) -> List[Document]:
    """
    Hybrid retrieval via Azure AI Search: dense (vector) + sparse (BM25 full-text),
    fused server-side with Azure's built-in RRF when both sides are used.

    alpha=1.0 -> vector-only, alpha=0.0 -> keyword-only, anything in between -> hybrid.
    score_threshold filters hits below that relevance score (@search.score) — note the
    score scale differs between modes (cosine-like for vector-only, RRF-fused for hybrid,
    BM25-like for keyword-only), so tune this per alpha rather than assuming one value
    fits all modes.
    """
    search_text = None if alpha >= 1.0 else query

    vector_queries = None
    if alpha > 0.0:
        query_vector = embeddings.embed_query(query)
        vector_queries = [
            VectorizedQuery(vector=query_vector, k_nearest_neighbors=fetch_k, fields="content_vector")
        ]

    results = get_search_client().search(
        search_text=search_text,
        vector_queries=vector_queries,
        top=fetch_k,
        select=_SELECT_FIELDS,
    )
    hits = list(results)

    if not hits:
        return []

    # Low-confidence guard: if the best hit is below the threshold, the query
    # has no relevant grounding in the knowledge base.
    if max(hit["@search.score"] for hit in hits) < settings.confidence_threshold:
        return []

    hits = [hit for hit in hits if hit["@search.score"] >= score_threshold][:k]

    return [
        Document(
            page_content=hit["content"],
            metadata={
                "source": hit.get("source"),
                "filename": hit.get("filename"),
                "source_type": hit.get("source_type"),
                "page": hit.get("page"),
                "chunk_index": hit.get("chunk_index"),
                "doc_id": hit.get("doc_id"),
            },
        )
        for hit in hits
    ]
