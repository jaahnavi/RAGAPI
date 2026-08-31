# fetches allowlisted CMS/Medicare PDFs into Azure Blob Storage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_container
from app.repositories import document_repository as repo
from app.services.documentservice import download_pdf
from app.ingest.pipeline import run_pipeline_background

SEED_URLS = [
    "https://www.medicare.gov/publications/10050-le-medicare-and-you.pdf",
    "https://www.medicare.gov/publications/10050-medicare-and-you.pdf",
    "https://www.cms.gov/medicare/prescription-drug-coverage/limitedincomeandresources/downloads/consumer-mailings.pdf",
    "https://www.medicare.gov/publications/11525-medicare-appeals.pdf",
]

def run():
    container = get_container()
    for url in SEED_URLS:
        print(f"Downloading: {url}")
        doc, is_new = download_pdf(url, container)
        if is_new:
            run_pipeline_background(doc.id)
            doc = repo.get_by_id(container, doc.id)
            print(f"Ingested: {doc.filename} (status: {doc.status})")
        else:
            print(f"Already exists: {doc.filename}")

if __name__ == "__main__":
    run()
