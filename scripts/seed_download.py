# fetches allowlisted CMS/Medicare PDFs into data/seed/
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
import app.models.document  # ensure models are registered before create_all
from app.services.documentservice import download_pdf
from app.ingest.pipeline import run_pipeline

Base.metadata.create_all(bind=engine)

SEED_URLS = [
    "https://www.medicare.gov/publications/10050-le-medicare-and-you.pdf",
    "https://www.medicare.gov/publications/10050-medicare-and-you.pdf",
    "https://www.cms.gov/medicare/prescription-drug-coverage/limitedincomeandresources/downloads/consumer-mailings.pdf",
    "https://www.medicare.gov/publications/11525-medicare-appeals.pdf",
]

def run():
    db = SessionLocal()
    try:
        for url in SEED_URLS:
            print(f"Downloading: {url}")
            doc, is_new = download_pdf(url, db)
            if is_new:
                run_pipeline(doc, db)
                print(f"Ingested: {doc.filename} (status: {doc.status})")
            else:
                print(f"Already exists: {doc.filename}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
