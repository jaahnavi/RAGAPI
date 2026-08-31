from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List

from app.config import settings
from app.store.vector_store import get_search_client

embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.azure_openai_embedding_api_key or "not-set",
    base_url=settings.azure_openai_embedding_endpoint,
)

def embed_and_store(chunks: List[Document], doc_id: str) -> None:
    """
    Embeds chunks and upserts them into the Azure AI Search index, tagged
    with doc_id so a document's chunks can be found and deleted together.
    """
    if not chunks:
        return

    for chunk in chunks:
        chunk.metadata["doc_id"] = doc_id

    vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])

    search_docs = [
        {
            "id": f"{doc_id}-{chunk.metadata.get('chunk_index', i)}",
            "content": chunk.page_content,
            "content_vector": vector,
            "doc_id": doc_id,
            "filename": chunk.metadata.get("filename") or "",
            "source": chunk.metadata.get("source") or "",
            "source_type": chunk.metadata.get("source_type") or "",
            "page": chunk.metadata.get("page") or 0,
            "chunk_index": chunk.metadata.get("chunk_index", i),
        }
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    get_search_client().upload_documents(documents=search_docs)
