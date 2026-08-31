import os
import tempfile
from pathlib import Path

from app.ingest.parser import extract_text_from_pdf
from app.ingest.chunker import chunk_text
from app.ingest.embedder import embed_and_store
from app.database import get_container
from app.repositories import document_repository as repo
from app.storage.azure_blob import download_blob


def run_pipeline_background(doc_id: str) -> None:
    container = get_container()
    try:
        doc = repo.get_by_id(container, doc_id)

        if doc is None:
            return

        blob_name = doc.filepath
        filename = doc.filename
        source_type = doc.source_type

        repo.update_status(container, doc, status="processing")

        content = download_blob(blob_name)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            pages = extract_text_from_pdf(Path(tmp_path))
        finally:
            os.remove(tmp_path)

        # Stamp original filename and source type on every page before chunking
        for page in pages:
            page.metadata["source"] = filename
            page.metadata["filename"] = filename
            page.metadata["source_type"] = source_type  # "seed" or "upload"


        chunks = chunk_text(pages)

        # Add chunk_index after splitting so each chunk has a unique position
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i

        embed_and_store(chunks, doc_id)

        doc = repo.get_by_id(container, doc_id)
        if doc is None:
            return
        repo.update_status(container, doc, status="ready")

    except Exception as e:
        doc = repo.get_by_id(container, doc_id)

        if doc is not None:
            repo.update_status(container, doc, status="failed", error=str(e))

        raise
