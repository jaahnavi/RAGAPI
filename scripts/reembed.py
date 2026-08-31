"""
Re-embed all documents already in blob storage with the current embedding model.

Run this whenever you change the embedding model so the vector store stays
consistent with the embeddings code.

Usage:
    python scripts/reembed.py
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_container
from app.repositories import document_repository as repo
from app.ingest.pipeline import run_pipeline_background
from app.store.vector_store import create_index, delete_index


def run():
    # 1. Wipe the old index — incompatible with new embedding dimensions
    print("Recreating the Azure AI Search index...")
    delete_index()
    create_index()

    container = get_container()
    docs = repo.list_all(container)
    if not docs:
        print("No documents in database. Run scripts/seed_download.py first.")
        return

    failed = 0
    for doc in docs:
        print(f"\nRe-embedding: {doc.filename}")
        try:
            run_pipeline_background(doc.id)
            print(f"Done: {doc.filename}")
        except Exception as e:
            print(f"Failed: {doc.filename} — {e}")
            failed += 1

    succeeded = len(docs) - failed
    print(f"\nFinished. {succeeded} document(s) re-embedded, {failed} failed.")


if __name__ == "__main__":
    run()
