# FastAPI entry point, mounts all routers

from fastapi import FastAPI
from app.api.documents import router as documents_router

app = FastAPI(title="Health Insurance RAG")

app.include_router(documents_router)