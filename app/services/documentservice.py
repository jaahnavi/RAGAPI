import hashlib
import os
import uuid
import requests
from urllib.parse import urlparse
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.document import Documents

SEED_DIR = "data/seed"
UPLOAD_DIR = "data/uploads"

os.makedirs(SEED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = {"medicare.gov", "cms.gov", "healthcare.gov"}


def _extract_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = os.path.basename(path)
    return name if name.endswith(".pdf") else f"{name}.pdf"


def download_pdf(url: str, db: Session) -> tuple[Documents, bool]:
    existing = db.query(Documents).filter(Documents.source_url == url).first()
    if existing:
        return existing, False

    response = requests.get(url, timeout=60, stream=True)
    if response.status_code != 200:
        raise Exception(f"Download failed for {url}: HTTP {response.status_code}")

    content = response.content

    if not content.startswith(b"%PDF"):
        raise Exception(f"URL did not return a valid PDF: {url}")

    content_hash = hashlib.sha256(content).hexdigest()

    existing_by_hash = db.query(Documents).filter(Documents.content_hash == content_hash).first()
    if existing_by_hash:
        return existing_by_hash, False

    file_uuid = str(uuid.uuid4())
    original_filename = _extract_filename_from_url(url)
    filepath = os.path.join(SEED_DIR, f"{file_uuid}.pdf")

    with open(filepath, "wb") as f:
        f.write(content)

    doc = Documents(
        uuid=file_uuid,
        filename=original_filename,
        filepath=filepath,
        source_url=url,
        content_hash=content_hash,
        source_type="seed",
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc, True


async def save_uploaded_pdf(file: UploadFile, db: Session) -> tuple[Documents, bool]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise Exception("Only PDF files are accepted. Please upload a .pdf file.")

    content = await file.read()

    if not content.startswith(b"%PDF"):
        raise Exception("Uploaded file is not a valid PDF.")

    content_hash = hashlib.sha256(content).hexdigest()

    existing = db.query(Documents).filter(Documents.content_hash == content_hash).first()
    if existing:
        return existing, False

    file_uuid = str(uuid.uuid4())
    original_filename = file.filename
    filepath = os.path.join(UPLOAD_DIR, f"{file_uuid}.pdf")

    with open(filepath, "wb") as f:
        f.write(content)

    doc = Documents(
        uuid=file_uuid,
        filename=original_filename,
        filepath=filepath,
        source_url=None,
        content_hash=content_hash,
        source_type="upload",
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc, True
