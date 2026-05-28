# fetches allowlisted CMS/Medicare PDFs into data/seed/
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingest.download import download_pdf

SEED_URLS = [
    "https://www.medicare.gov/publications/10050-le-medicare-and-you.pdf",
    "https://www.medicare.gov/publications/10050-medicare-and-you.pdf",
    "https://www.cms.gov/medicare/prescription-drug-coverage/limitedincomeandresources/downloads/consumer-mailings.pdf"
]

def run():
    for url in SEED_URLS:
        print(f"Downloading: {url}")
        result = download_pdf(url)
        print(f"Saved: {result['filename']}")

if __name__ == "__main__":
    run()