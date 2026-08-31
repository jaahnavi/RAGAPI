# Prints the first few documents in the Azure AI Search index, for debugging.
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.store.vector_store import get_search_client

results = get_search_client().search(search_text="*", top=5, select=["id", "doc_id", "filename", "page", "chunk_index", "content"])

for hit in results:
    print("=" * 80)
    print("ID:", hit["id"])
    print("DOC_ID:", hit["doc_id"], "| FILENAME:", hit["filename"], "| PAGE:", hit["page"], "| CHUNK:", hit["chunk_index"])
    print("CONTENT:")
    print(hit["content"][:300])
    print()
