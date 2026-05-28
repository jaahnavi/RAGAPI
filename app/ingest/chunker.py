# text → chunks with metadata (size, overlap)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List


def chunk_text(pages: List[Document], chunk_size: int = 512, overlap: int = 64) -> List[Document]:
    """
    Takes LangChain Document objects from parser.py and splits them into chunks.
    Metadata (source, page number) is carried through automatically.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""]  # tries to split on natural boundaries first
    )

    chunks = splitter.split_documents(pages)
    return chunks