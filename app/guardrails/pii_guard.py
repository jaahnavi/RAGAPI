"""
PII / PSI guardrails for the health-insurance RAG API.

PII (Personally Identifiable Information) — detected by regex, masked before
the LLM sees the text and again before the response reaches the caller:
  • SSN, credit card, email, US phone, date-of-birth,
    Medicare Beneficiary ID (MBI), bank account numbers

PSI (Personally Sensitive Information) — detected by keyword heuristics,
flagged only (not blocked), because a health-insurance assistant is expected
to discuss medical topics:
  • Medical conditions / diagnoses
  • Mental health references
  • Financial distress indicators
  • Immigration / legal status

Usage
-----
    from app.guardrails.pii_guard import scan_input, scan_output, apply_guardrails

    masked_q, pii_q, psi_cats = scan_input(question)
    # ... call LLM with masked_q ...
    masked_a, pii_a = scan_output(answer)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ── PII patterns ──────────────────────────────────────────────────────────────

_PII_PATTERNS: Dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "phone_us": re.compile(r"\b(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4}\b"),
    "dob": re.compile(
        r"\b(?:0?[1-9]|1[0-2])[/\-](?:0?[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b"
    ),
    # Medicare Beneficiary ID — 11-char alphanumeric, e.g. 1EG4-TE5-MK72
    "medicare_mbi": re.compile(
        r"\b[1-9][A-Z][A-Z0-9]{1}[-][A-Z][A-Z0-9]{1}[-][A-Z0-9]{3}\b",
        re.IGNORECASE,
    ),
    "bank_account": re.compile(
        r"\b(?:account|acct|acc)[\s#:]*(\d{6,17})\b",
        re.IGNORECASE,
    ),
}

_MASK: Dict[str, str] = {
    "ssn":          "[SSN REDACTED]",
    "credit_card":  "[CC REDACTED]",
    "email":        "[EMAIL REDACTED]",
    "phone_us":     "[PHONE REDACTED]",
    "dob":          "[DOB REDACTED]",
    "medicare_mbi": "[MBI REDACTED]",
    "bank_account": "[ACCT REDACTED]",
}


# ── PSI keywords ──────────────────────────────────────────────────────────────

_PSI_KEYWORDS: Dict[str, List[str]] = {
    "medical_condition": [
        "cancer", "diabetes", "hiv", "aids", "depression", "anxiety",
        "schizophrenia", "bipolar", "epilepsy", "autism", "adhd",
        "dementia", "alzheimer", "diagnosis", "diagnosed", "disorder",
        "disease", "syndrome", "chronic", "terminal",
    ],
    "mental_health": [
        "therapy", "therapist", "psychiatrist", "antidepressant",
        "mental health", "suicidal", "self-harm", "substance abuse", "addiction",
    ],
    "financial_distress": [
        "bankrupt", "bankruptcy", "debt", "foreclosure", "poverty",
        "low income", "unable to pay", "can't afford", "cannot afford",
    ],
    "immigration": [
        "undocumented", "green card", "visa status", "immigration status",
        "citizenship status", "daca", "work permit",
    ],
}


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class GuardrailResult:
    sanitized_question: str
    sanitized_answer: str
    pii_types_in_question: List[str] = field(default_factory=list)
    pii_types_in_answer: List[str] = field(default_factory=list)
    psi_categories_in_question: List[str] = field(default_factory=list)

    @property
    def pii_detected(self) -> bool:
        return bool(self.pii_types_in_question or self.pii_types_in_answer)

    @property
    def psi_detected(self) -> bool:
        return bool(self.psi_categories_in_question)

    @property
    def all_pii_types(self) -> List[str]:
        return list(set(self.pii_types_in_question + self.pii_types_in_answer))


# ── Core helpers ──────────────────────────────────────────────────────────────

def _mask_pii(text: str) -> Tuple[str, List[str]]:
    """Replace PII tokens with redaction placeholders. Returns (masked_text, [types_found])."""
    found: List[str] = []
    for name, pattern in _PII_PATTERNS.items():
        if pattern.search(text):
            found.append(name)
            text = pattern.sub(_MASK[name], text)
    return text, found


def _detect_psi(text: str) -> List[str]:
    lower = text.lower()
    return [
        category
        for category, keywords in _PSI_KEYWORDS.items()
        if any(kw in lower for kw in keywords)
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def scan_input(question: str) -> Tuple[str, List[str], List[str]]:
    """
    Scan and sanitize an incoming user question before it reaches the LLM.

    Returns:
        masked_question  — question with PII replaced by redaction tokens
        pii_types        — list of PII category names found (e.g. ["ssn"])
        psi_categories   — list of PSI category names found (e.g. ["medical_condition"])
    """
    masked_q, pii_types = _mask_pii(question)
    psi_cats = _detect_psi(question)
    return masked_q, pii_types, psi_cats


def scan_output(answer: str) -> Tuple[str, List[str]]:
    """
    Scan and sanitize an LLM-generated answer before it is returned to the caller.

    Returns:
        masked_answer  — answer with any echoed PII replaced by redaction tokens
        pii_types      — list of PII category names found in the answer
    """
    return _mask_pii(answer)


def apply_guardrails(question: str, answer: str) -> GuardrailResult:
    """
    Convenience wrapper: scan both question and answer in one call.

    Callers that need to use the masked question *before* generating the answer
    should call scan_input() / scan_output() separately.
    """
    masked_q, pii_q, psi_cats = scan_input(question)
    masked_a, pii_a = scan_output(answer)
    return GuardrailResult(
        sanitized_question=masked_q,
        sanitized_answer=masked_a,
        pii_types_in_question=pii_q,
        pii_types_in_answer=pii_a,
        psi_categories_in_question=psi_cats,
    )
