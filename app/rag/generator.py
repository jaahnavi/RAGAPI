from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings

LLM_MODEL = settings.llm_model

_SYSTEM_PROMPT = """\
You are a health insurance specialist assistant. Answer the user's question \
using ONLY the context provided below.

Rules:
- Cite each claim with its source using [Doc N] notation (e.g. "the deductible is $500 [Doc 1]").
- If the answer cannot be found in the context, reply exactly:
  "I don't have enough information in the provided documents to answer that."
- Never speculate or add information beyond what the context contains.
- Be concise and precise."""

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

_llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0,
    api_key=settings.azure_openai_chat_api_key or "not-set",
    base_url=settings.azure_openai_chat_endpoint,
    use_responses_api=True,
)
_chain = _prompt | _llm | StrOutputParser()


def _format_context(docs: List[Document]) -> str:
    sections = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "")
        label = f"[Doc {i}] {source}" + (f", p.{page}" if page != "" else "")
        sections.append(f"{label}\n{doc.page_content}")
    return "\n\n".join(sections)


def generate_answer(question: str, docs: List[Document]) -> str:
    if not docs:
        return "I don't have enough information in the provided documents to answer that."
    return _chain.invoke({"context": _format_context(docs), "question": question})


def generate_answer_stream(question: str, docs: List[Document]):
    if not docs:
        yield "I don't have enough information in the provided documents to answer that."
        return
    for chunk in _chain.stream({"context": _format_context(docs), "question": question}):
        yield chunk
