import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import QueryRequest, QueryResponse
from app.services.chatservice import ask, stream_ask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=QueryResponse)
def chat(request: QueryRequest) -> QueryResponse:
    try:
        result = ask(request.message, k=request.k, alpha=request.alpha)
    except Exception:
        logger.exception("chat request failed")
        raise HTTPException(status_code=500, detail="Failed to generate an answer")
    return QueryResponse(**result)


@router.post("/stream")
def chat_stream(request: QueryRequest):
    def _guarded_stream():
        try:
            yield from stream_ask(request.message, k=request.k, alpha=request.alpha)
        except Exception:
            logger.exception("chat stream request failed")
            raise

    return StreamingResponse(_guarded_stream(), media_type="text/event-stream")
