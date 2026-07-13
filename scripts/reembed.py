"""
Re-embed all documents already on disk with the current embedding model.

Run this whenever you change the embedding model so the vector store stays
consistent with the embeddings code.

Usage:
    python scripts/reembed.py
"""
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine, Base
import app.models.document  # ensure model is registered
from app.models.document import Documents
from app.ingest.pipeline import run_pipeline
from app.ingest.embedder import CHROMA_DIR

Base.metadata.create_all(bind=engine)


def run():
    # 1. Wipe the old vector store — incompatible with new embedding dimensions
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print(f"Cleared ChromaDB at {CHROMA_DIR}")
    else:
        print("No existing ChromaDB found, starting fresh.")

    db = SessionLocal()
    try:
        docs = db.query(Documents).all()
        if not docs:
            print("No documents in database. Run scripts/seed_download.py first.")
            return

        skipped = 0
        for doc in docs:
            if not doc.filepath or not os.path.exists(doc.filepath):
                print(f"Skipping '{doc.filename}' — file not found at {doc.filepath}")
                skipped += 1
                continue

            print(f"\nRe-embedding: {doc.filename}")
            # Reset so run_pipeline transitions through its normal statuses
            doc.status = "pending"
            doc.error = None
            db.commit()

            run_pipeline(doc, db)
            print(f"Done: {doc.filename} (status: {doc.status})")

        succeeded = len(docs) - skipped
        print(f"\nFinished. {succeeded} document(s) re-embedded, {skipped} skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
