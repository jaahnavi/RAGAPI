# Creates (or updates) the Azure AI Search index used for document embeddings.
#
# Usage:
#     python scripts/create_search_index.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.config import settings
from app.store.vector_store import create_index


def run():
    print(f"Creating/updating index '{settings.azure_search_index_name}' at {settings.azure_search_endpoint} ...")
    create_index()
    print("Done.")


if __name__ == "__main__":
    run()
