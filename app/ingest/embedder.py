from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List

from app.config import settings

CHROMA_DIR = settings.chroma_dir

embeddings = OpenAIEmbeddings(model=settings.embedding_model)

def embed_and_store(chunks: List[Document], doc_id: str) -> None:
    """
    Embeds chunks and stores them in Chroma with doc_id in metadata.
    """
    # attach doc_id to each chunk's metadata
    for chunk in chunks:
        chunk.metadata["doc_id"] = doc_id

    vectorstore = Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir
    )

    vectorstore.add_documents(chunks)