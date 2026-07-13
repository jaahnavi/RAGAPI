from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.database import engine
from app.models.document import Documents
from app.database import Base
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Health Insurance RAG")
app.include_router(documents_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=True)
