# Pydantic request/response shapes

from pydantic import BaseModel, Field


class PDFRequest(BaseModel):
    url: str


class PDFResponse(BaseModel):
    success: bool
    filename: str
    filepath: str


class QueryRequest(BaseModel):
    message: str
    k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="Vector weight (0=BM25 only, 1=vector only)")


class SourceChunk(BaseModel):
    content: str
    metadata: dict


class GuardrailFlags(BaseModel):
    pii_detected: bool = False
    pii_types: list[str] = Field(default_factory=list)
    psi_detected: bool = False
    psi_categories: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    guardrail_flags: GuardrailFlags | None = None