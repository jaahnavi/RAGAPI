# POST /documents/upload, GET /documents, DELETE /documents/{id}

from fastapi import APIRouter, UploadFile, File
from app.models.schemas import PDFRequest
from app.ingest.download import download_pdf, save_uploaded_pdf

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload-url")
def upload_document(request: PDFRequest):
    result = download_pdf(request.url)
    return {
        "success": True,
        "data": result
    }

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = await save_uploaded_pdf(file)
    return {"success": True, "data": result}