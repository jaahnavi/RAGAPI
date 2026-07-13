# POST /documents/upload, GET /documents, DELETE /documents/{id}

import os
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.documentservice import download_pdf, save_uploaded_pdf
from app.ingest.pipeline import run_pipeline_background
from app.models.schemas import PDFRequest
from app.models.document import Documents
from langchain_chroma import Chroma
from app.ingest.embedder import embeddings, CHROMA_DIR

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload-url")
def upload_document(
    request: PDFRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    doc, is_new = download_pdf(request.url, db)
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
    db: Session = Depends(get_db),
):
    try:
        doc, is_new = await save_uploaded_pdf(file, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if is_new:
        background_tasks.add_task(run_pipeline_background, doc.id)
    return {
        "success": True,
        "already_exists": not is_new,
        "data": {"id": doc.id, "filename": doc.filename, "status": doc.status},
    }


@router.get("/")
def get_all_status(db: Session = Depends(get_db)):
    docs = db.query(Documents).order_by(Documents.created_at.desc()).all()
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
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Documents).filter(Documents.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    vectorstore = Chroma(
        collection_name="health_insurance",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    vectorstore.delete(where={"doc_id": doc_id})

    if doc.filepath and os.path.exists(doc.filepath):
        os.remove(doc.filepath)

    db.delete(doc)
    db.commit()
    return {"success": True, "deleted_id": doc_id}
