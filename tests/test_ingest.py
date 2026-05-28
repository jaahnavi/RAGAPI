#test ingest
from app.ingest.parser import extract_text_from_pdf
from app.ingest.chunker import chunk_text
from app.ingest.embedder import embed_and_store
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from pathlib import Path


pages = extract_text_from_pdf(Path("data/seed/5cd20507-0bad-4482-9197-db6bd3234ab1.pdf"))
chunks = chunk_text(pages)

print(f"Total chunks: {len(chunks)}")
for chunk in chunks[:10]:  
    print("---")
    print(chunk.page_content)
    print(chunk.metadata)


embed_and_store(chunks, doc_id=1)
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(
    collection_name="health_insurance",
    embedding_function=embeddings,
    persist_directory="data/chroma"
)

print(f"Total chunks in store: {vectorstore._collection.count()}")
