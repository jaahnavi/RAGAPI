# POST /documents/upload, GET /documents, DELETE /documents/{id}

from fastapi import APIRouter
from app.models.schemas import PDFRequest
from app.ingest.download import download_pdf

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
def upload_document(request: PDFRequest):
    result = download_pdf(request.url)
    return {
        "success": True,
        "data": result
    }