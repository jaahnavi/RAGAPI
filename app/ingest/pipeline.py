from sqlalchemy.orm import Session
from app.models.document import Documents
from app.ingest.parser import extract_text_from_pdf
from app.ingest.chunker import chunk_text
from app.ingest.embedder import embed_and_store
from pathlib import Path


def run_pipeline(doc: Documents, db: Session) -> None:
    try:
        doc.status = "processing"
        db.commit()

        pages = extract_text_from_pdf(Path(doc.filepath))

        # Stamp original filename and source type on every page before chunking
        for page in pages:
            page.metadata["source"] = doc.filename
            page.metadata["filename"] = doc.filename
            page.metadata["source_type"] = doc.source_type  # "seed" or "upload"

        chunks = chunk_text(pages)

        # Add chunk_index after splitting so each chunk has a unique position
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i

        embed_and_store(chunks, doc_id=doc.id)

        doc.status = "ready"
        db.commit()

    except Exception as e:
        doc.status = "failed"
        doc.error = str(e)
        db.commit()
        raise


def run_pipeline_background(doc_id: int) -> None:
    """Runs the ingestion pipeline in a background task with its own DB session."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if doc:
            run_pipeline(doc, db)
    finally:
        db.close()
