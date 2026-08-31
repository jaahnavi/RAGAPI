import hashlib
import os
import uuid
import requests
from urllib.parse import urlparse
from fastapi import UploadFile
from azure.cosmos.container import ContainerProxy
from app.config import settings
from app.models.document import Documents
from app.repositories import document_repository as repo
from app.storage.azure_blob import upload_blob

ALLOWED_DOMAINS = settings.allowed_download_domains

def _extract_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = os.path.basename(path)
    return name if name.endswith(".pdf") else f"{name}.pdf"


def download_pdf(url: str, container: ContainerProxy) -> tuple[Documents, bool]:
    existing = repo.get_by_source_url(container, url)
    if existing:
        return existing, False

    parsed = urlparse(url)

    if parsed.netloc not in ALLOWED_DOMAINS:
        raise Exception("Domain not allowed")

    response = requests.get(url, timeout=60, stream=True)
    if response.status_code != 200:
        raise Exception(f"Download failed for {url}: HTTP {response.status_code}")

    content = response.content

    if not content.startswith(b"%PDF"):
        raise Exception(f"URL did not return a valid PDF: {url}")

    content_hash = hashlib.sha256(content).hexdigest()

    existing_by_hash = repo.get_by_content_hash(container, content_hash)
    if existing_by_hash:
        return existing_by_hash, False

    doc_id = str(uuid.uuid4())
    original_filename = _extract_filename_from_url(url)
    blob_name = f"seed/{doc_id}.pdf"

    blob_url = upload_blob(blob_name, content)

    doc = Documents(
        id=doc_id,
        filename=original_filename,
        filepath=blob_url,
        source_url=url,
        content_hash=content_hash,
        source_type="seed",
        status="processing",
    )
    doc = repo.create(container, doc)

    return doc, True


async def save_uploaded_pdf(file: UploadFile, container: ContainerProxy) -> tuple[Documents, bool]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise Exception("Only PDF files are accepted. Please upload a .pdf file.")

    content = await file.read()

    if not content.startswith(b"%PDF"):
        raise Exception("Uploaded file is not a valid PDF.")

    content_hash = hashlib.sha256(content).hexdigest()

    existing = repo.get_by_content_hash(container, content_hash)
    if existing:
        return existing, False

    doc_id = str(uuid.uuid4())
    original_filename = file.filename
    blob_name = f"uploads/{doc_id}.pdf"

    blob_url = upload_blob(blob_name, content)

    doc = Documents(
        id=doc_id,
        filename=original_filename,
        filepath=blob_url,
        source_url=None,
        content_hash=content_hash,
        source_type="upload",
        status="processing",
    )
    doc = repo.create(container, doc)

    return doc, True
