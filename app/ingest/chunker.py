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

"""
#check if better chunking is required after the evaluators
# Step 1 - split by headers first (coarse splits)
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2")]
)
header_chunks = markdown_splitter.split_text(text)

# Step 2 - semantically rechunk anything too large
semantic_splitter = SemanticChunker(embeddings)
final_chunks = []
for chunk in header_chunks:
    if len(chunk.page_content) > 1000:
        final_chunks.extend(semantic_splitter.create_documents([chunk.page_content]))
    else:
        final_chunks.append(chunk)
"""