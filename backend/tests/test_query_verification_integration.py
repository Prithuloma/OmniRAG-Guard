"""
tests/test_query_verification_integration.py
--------------------------------------------
Integration tests for retrieval + LLM + verification in the query pipeline.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.models.request_models import QueryRequest
from app.services.llm.llm_models import LLMGenerationResult
from app.services.llm.llm_service import LLMService
from app.services.llm.mock_llm import MockLLM
from app.services.query_service import QueryService, to_query_response
from app.services.retrieval_service import RetrievalResult, RetrievedChunk
from app.services.verification.verification_models import VerificationResult
from app.services.verification.verification_service import (
    EVIDENCE_CONFIDENCE_WEIGHT,
    RETRIEVAL_CONFIDENCE_WEIGHT,
    SUPPORTED_REASON,
    VerificationService,
)


def _success_retrieval_result(*, query: str) -> RetrievalResult:
    return RetrievalResult(
        query=query,
        status="success",
        chunks=[
            RetrievedChunk(
                chunk_id="doc-1:chunk:0",
                document_id="doc-1",
                page_number=1,
                text="OmniRAG-Guard is a FastAPI-based RAG system.",
                score=0.88,
            )
        ],
    )


@pytest.fixture
def retrieval_service() -> AsyncMock:
    service = AsyncMock()
    service.retrieve.return_value = _success_retrieval_result(
        query="What is this document about?"
    )
    return service


@pytest.mark.asyncio
async def test_query_pipeline_includes_verification_fields(
    retrieval_service: AsyncMock,
) -> None:
    service = QueryService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(provider=MockLLM()),
        verification_service=VerificationService(),
    )

    result = await service.execute_query(
        QueryRequest(query="What is this document about?", top_k=5)
    )

    assert result.status == "success"
    assert result.answer
    assert result.evidence_score >= 0.5
    assert result.grounded is True
    assert result.verification_reason == SUPPORTED_REASON
    assert result.confidence == pytest.approx(
        RETRIEVAL_CONFIDENCE_WEIGHT * 0.88
        + EVIDENCE_CONFIDENCE_WEIGHT * result.evidence_score
    )


@pytest.mark.asyncio
async def test_query_response_exposes_verification_metadata(
    retrieval_service: AsyncMock,
) -> None:
    service = QueryService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(provider=MockLLM()),
        verification_service=VerificationService(),
    )

    pipeline_result = await service.execute_query(
        QueryRequest(query="What is this document about?")
    )
    response = to_query_response(pipeline_result)

    assert response.answer
    assert response.evidence_score >= 0.5
    assert response.grounded is True
    assert response.verification_reason == SUPPORTED_REASON
    assert response.confidence == pipeline_result.confidence


@pytest.mark.asyncio
async def test_query_pipeline_uses_injected_verification_service(
    retrieval_service: AsyncMock,
) -> None:
    verification_service = AsyncMock()
    verification_service.verify.return_value = VerificationResult(
        evidence_score=0.82,
        grounded=True,
        verification_reason=SUPPORTED_REASON,
        confidence=0.85,
        retrieval_confidence=0.88,
    )

    service = QueryService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(provider=MockLLM()),
        verification_service=verification_service,
    )

    result = await service.execute_query(
        QueryRequest(query="What is this document about?")
    )

    assert result.confidence == pytest.approx(0.85)
    assert result.evidence_score == pytest.approx(0.82)
    assert result.grounded is True
    verification_service.verify.assert_awaited_once()
