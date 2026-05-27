import os
import uuid
import requests

PDF_DIR = "data/seed"
os.makedirs(PDF_DIR, exist_ok=True)

def download_pdf(url: str) -> dict:
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Download failed for {url}")

    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(response.content)

    return {
        "filename": filename,
        "filepath": filepath
    }