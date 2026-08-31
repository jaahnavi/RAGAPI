# POST /documents/upload, GET /documents, DELETE /documents/{id}

import logging
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Depends, HTTPException
from azure.cosmos.container import ContainerProxy

from app.database import get_db
from app.services.documentservice import download_pdf, save_uploaded_pdf
from app.ingest.pipeline import run_pipeline_background
from app.models.schemas import PDFRequest
from app.repositories import document_repository as repo
from app.storage.azure_blob import delete_blob
from app.store.vector_store import delete_by_doc_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload-url")
def upload_document(
    request: PDFRequest,
    background_tasks: BackgroundTasks,
    container: ContainerProxy = Depends(get_db),
):

    doc, is_new = download_pdf(request.url, container)
    if is_new:
        background_tasks.add_task(run_pipeline_background, doc.id)
    return {
        "success": True,
        "already_exists": not is_new,
        "data": {"id": doc.id, "filename": doc.filename, "status": doc.status},
    }


@router.post("/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    container: ContainerProxy = Depends(get_db),
):
    try:
        doc, is_new = await save_uploaded_pdf(file, container)
    except Exception as e:
        logger.warning("file upload rejected: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    if is_new:
        background_tasks.add_task(run_pipeline_background, doc.id)
    return {
        "success": True,
        "already_exists": not is_new,
        "data": {"id": doc.id, "filename": doc.filename, "status": doc.status},
    }


@router.get("/")
def get_all_status(container: ContainerProxy = Depends(get_db)):
    docs = repo.list_all(container)
    return {
        "total": len(docs),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "source_type": doc.source_type,
                "source_url": doc.source_url,
                "status": doc.status,
                "error": doc.error,
                "created_at": doc.created_at,
            }
            for doc in docs
        ],
    }


@router.delete("/{doc_id}")
def delete_document(doc_id: str, container: ContainerProxy = Depends(get_db)):
    doc = repo.get_by_id(container, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        delete_by_doc_id(doc_id)
    except Exception:
        logger.exception("failed to delete vectors for doc_id=%s", doc_id)
        raise HTTPException(status_code=500, detail="Failed to delete document vectors")

    if doc.filepath:
        try:
            delete_blob(doc.filepath)
        except Exception:
            logger.exception("failed to remove blob %s for doc_id=%s", doc.filepath, doc_id)

    repo.delete(container, doc_id)
    return {"success": True, "deleted_id": doc_id}
