# Pydantic request/response shapes

from pydantic import BaseModel

class PDFRequest(BaseModel):
    url: str

class PDFResponse(BaseModel):
    success: bool
    filename: str
    filepath: str