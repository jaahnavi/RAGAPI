import json
from typing import Any, Generator

from app.guardrails.pii_guard import scan_input, scan_output
from app.rag.retriever import hybrid_search
from app.rag.generator import generate_answer, generate_answer_stream

try:
    from langsmith import traceable
except ImportError:
    def traceable(**_kwargs):
        def decorator(fn):
            return fn
        return decorator


@traceable(name="rag-chat", project_name="health-insurance-rag")
def ask(question: str, k: int = 5, alpha: float = 0.5) -> dict[str, Any]:
    # Input guardrail: mask PII before it reaches the retriever / LLM
    masked_q, pii_q, psi_cats = scan_input(question)

    docs = hybrid_search(masked_q, k=k, alpha=alpha)
    answer = generate_answer(masked_q, docs)

    # Output guardrail: mask any PII that leaked into the generated answer
    masked_a, pii_a = scan_output(answer)

    sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    return {
        "answer": masked_a,
        "sources": sources,
        "guardrail_flags": {
            "pii_detected": bool(pii_q or pii_a),
            "pii_types": list(set(pii_q + pii_a)),
            "psi_detected": bool(psi_cats),
            "psi_categories": psi_cats,
        },
    }


@traceable(name="rag-chat-stream", project_name="health-insurance-rag")
def stream_ask(question: str, k: int = 5, alpha: float = 0.5) -> Generator[str, None, None]:
    # Input guardrail applied; output masking is best-effort for streaming
    masked_q, pii_q, psi_cats = scan_input(question)

    docs = hybrid_search(masked_q, k=k, alpha=alpha)
    sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    guardrail_flags = {
        "pii_detected": bool(pii_q),
        "pii_types": pii_q,
        "psi_detected": bool(psi_cats),
        "psi_categories": psi_cats,
    }
    for token in generate_answer_stream(masked_q, docs):
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield f"data: {json.dumps({'sources': sources, 'guardrail_flags': guardrail_flags, 'done': True})}\n\n"
