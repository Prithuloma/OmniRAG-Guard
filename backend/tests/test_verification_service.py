"""
tests/test_verification_service.py
----------------------------------
Unit tests for the verification layer.
"""

from __future__ import annotations

import pytest

from app.services.retrieval_service import RetrievedChunk
from app.services.verification.lexical_scorer import compute_lexical_evidence_score
from app.services.verification.verification_service import (
    EVIDENCE_CONFIDENCE_WEIGHT,
    INSUFFICIENT_OVERLAP_REASON,
    RETRIEVAL_CONFIDENCE_WEIGHT,
    SUPPORTED_REASON,
    VerificationService,
)


def _make_chunk(*, text: str, score: float = 0.88) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="doc-1:chunk:0",
        document_id="doc-1",
        page_number=1,
        text=text,
        score=score,
    )


def test_lexical_overlap_detects_shared_terms() -> None:
    score = compute_lexical_evidence_score(
        "Revenue increased by 18 percent year over year.",
        ["Revenue increased by 18 percent in the latest quarter."],
    )

    assert score > 0.5


def test_lexical_overlap_returns_zero_for_unrelated_answer() -> None:
    score = compute_lexical_evidence_score(
        "Quantum computing will transform cryptography.",
        ["Revenue increased by 18 percent year over year."],
    )

    assert score == 0.0


@pytest.mark.asyncio
async def test_verification_marks_grounded_answer() -> None:
    service = VerificationService(grounded_threshold=0.5)
    chunks = [
        _make_chunk(
            text="OmniRAG-Guard is a FastAPI-based RAG system.",
            score=0.88,
        )
    ]
    answer = (
        "Based on the retrieved documents, OmniRAG-Guard is a FastAPI-based RAG system. "
        "This addresses the question: What is this document about?"
    )

    result = await service.verify(
        query="What is this document about?",
        generated_answer=answer,
        retrieved_chunks=chunks,
    )

    assert result.grounded is True
    assert result.evidence_score >= 0.5
    assert result.verification_reason == SUPPORTED_REASON
    assert result.retrieval_confidence == pytest.approx(0.88)
    assert result.confidence == pytest.approx(
        RETRIEVAL_CONFIDENCE_WEIGHT * 0.88 + EVIDENCE_CONFIDENCE_WEIGHT * result.evidence_score
    )


@pytest.mark.asyncio
async def test_verification_marks_ungrounded_answer() -> None:
    service = VerificationService(grounded_threshold=0.5)
    chunks = [_make_chunk(text="Revenue increased by 18 percent year over year.")]

    result = await service.verify(
        query="What drove growth?",
        generated_answer="Quantum computing will transform cryptography.",
        retrieved_chunks=chunks,
    )

    assert result.grounded is False
    assert result.evidence_score == 0.0
    assert result.verification_reason == INSUFFICIENT_OVERLAP_REASON
    assert result.confidence == pytest.approx(RETRIEVAL_CONFIDENCE_WEIGHT * 0.88)


@pytest.mark.asyncio
async def test_verification_handles_empty_answer() -> None:
    service = VerificationService()
    chunks = [_make_chunk(text="Some context.")]

    result = await service.verify(
        query="test",
        generated_answer="   ",
        retrieved_chunks=chunks,
    )

    assert result.grounded is False
    assert result.evidence_score == 0.0
    assert result.confidence == 0.0
