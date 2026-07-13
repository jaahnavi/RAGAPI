from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import QueryRequest, QueryResponse
from app.services.chatservice import ask, stream_ask

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=QueryResponse)
def chat(request: QueryRequest) -> QueryResponse:
    result = ask(request.message, k=request.k, alpha=request.alpha)
    return QueryResponse(**result)


@router.post("/stream")
def chat_stream(request: QueryRequest):
    return StreamingResponse(
        stream_ask(request.message, k=request.k, alpha=request.alpha),
        media_type="text/event-stream",
    )
