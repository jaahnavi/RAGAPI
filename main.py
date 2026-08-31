from dotenv import load_dotenv
load_dotenv()

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

from fastapi import FastAPI
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router

# The Cosmos DB container connects lazily on first use (see app.database.get_container),
# so no eager connection is made here — this keeps app startup import-safe for tests
# that override the get_db dependency.
app = FastAPI(title="Health Insurance RAG")
app.include_router(documents_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=True)
