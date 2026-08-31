from __future__ import annotations

import re
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi

from app.config import settings

embeddings = OpenAIEmbeddings(model=settings.embedding_model)


def _get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir,
    )


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def hybrid_search(
    query: str,
    k: int = 10,
    fetch_k: int = 20,
    alpha: float = 0.5,
    score_threshold: float = settings.score_threshold,
) -> List[Document]:
    """
    Hybrid retrieval: dense (Chroma cosine) + sparse (BM25) fused via RRF.

    alpha=1.0 → pure vector, alpha=0.0 → pure BM25.
    score_threshold filters vector hits below that relevance score before fusion.
    """
    vectorstore = _get_vectorstore()

    # Load full corpus once — needed to build BM25 index and reconstruct docs
    corpus = vectorstore.get(include=["documents", "metadatas"])  # ids always returned
    texts: List[str] = corpus["documents"]
    metadatas: List[dict] = corpus["metadatas"]
    chroma_ids: List[str] = corpus["ids"]

    if not texts:
        return []

    # O(1) content lookup to map LangChain docs back to their Chroma ID
    content_to_chroma_id = {text: chroma_ids[i] for i, text in enumerate(texts)}
    chroma_id_to_idx = {cid: i for i, cid in enumerate(chroma_ids)}

    # --- Dense retrieval ---
    vector_hits = vectorstore.similarity_search_with_relevance_scores(query, k=fetch_k)

    # Low-confidence guard: if the best vector score is below the threshold,
    # the query has no relevant grounding in the knowledge base.
    if not vector_hits or max(score for _, score in vector_hits) < settings.confidence_threshold:
        return []

    vector_hits = [(doc, score) for doc, score in vector_hits if score >= score_threshold]

    # --- Sparse retrieval (BM25) ---
    bm25 = BM25Okapi([_tokenize(t) for t in texts])
    bm25_scores = bm25.get_scores(_tokenize(query))
    top_bm25_idx = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:fetch_k]

    # --- Reciprocal Rank Fusion ---
    # Skip a side entirely when its weight is zero — otherwise its docs would
    # still be inserted into rrf with a 0.0 score, leaking past filters like
    # score_threshold (which only applies to the vector side).
    rrf: dict[str, float] = {}

    if alpha > 0:
        for rank, (doc, _) in enumerate(vector_hits):
            cid = content_to_chroma_id.get(doc.page_content)
            if cid is None:
                continue
            rrf[cid] = rrf.get(cid, 0.0) + alpha / (settings.rrf_k + rank + 1)

    if alpha < 1:
        for rank, idx in enumerate(top_bm25_idx):
            cid = chroma_ids[idx]
            rrf[cid] = rrf.get(cid, 0.0) + (1.0 - alpha) / (settings.rrf_k + rank + 1)

    # Sort by fused score and reconstruct Documents
    top_cids = sorted(rrf, key=lambda c: rrf[c], reverse=True)[:k]
    return [
        Document(
            page_content=texts[chroma_id_to_idx[cid]],
            metadata=metadatas[chroma_id_to_idx[cid]],
        )
        for cid in top_cids
    ]
