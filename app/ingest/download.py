import os
import uuid
import requests
from fastapi import UploadFile

SEED_DIR = "data/seed"
UPLOAD_DIR = "data/uploads"

os.makedirs(SEED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def download_pdf(url: str) -> dict:
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Download failed for {url}")

    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(SEED_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(response.content)

    return {
        "filename": filename,
        "filepath": filepath
    }

async def save_uploaded_pdf(file: UploadFile) -> dict:
    if not file.filename.endswith(".pdf"):
        raise Exception("Only PDF files are accepted")

    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "filename": filename, 
        "filepath": filepath
    }