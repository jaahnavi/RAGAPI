from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List

CHROMA_DIR = "data/chroma"

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def embed_and_store(chunks: List[Document], doc_id: int) -> None:
    """
    Embeds chunks and stores them in Chroma with doc_id in metadata.
    """
    # attach doc_id to each chunk's metadata
    for chunk in chunks:
        chunk.metadata["doc_id"] = doc_id

    vectorstore = Chroma(
        collection_name="health_insurance",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

    vectorstore.add_documents(chunks)