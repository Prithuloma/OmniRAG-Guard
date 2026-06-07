"""
tests/test_query_llm_integration.py
-----------------------------------
Integration tests for retrieval + LLM answer generation in the query pipeline.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.models.request_models import QueryRequest
from app.services.llm.llm_models import LLMGenerationResult
from app.services.llm.llm_service import LLMService
from app.services.llm.mock_llm import MockLLM
from app.services.query_service import QueryPipelineErrorCode, QueryService, to_query_response
from app.services.retrieval_service import RetrievalResult, RetrievedChunk


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
async def test_query_pipeline_generates_answer_after_retrieval(
    retrieval_service: AsyncMock,
) -> None:
    service = QueryService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(provider=MockLLM()),
    )

    result = await service.execute_query(
        QueryRequest(query="What is this document about?", top_k=5)
    )

    assert result.status == "success"
    assert result.chunk_count == 1
    assert result.answer
    assert "OmniRAG-Guard is a FastAPI-based RAG system" in result.answer
    assert result.confidence == pytest.approx(0.88)


@pytest.mark.asyncio
async def test_query_response_includes_generated_answer(
    retrieval_service: AsyncMock,
) -> None:
    service = QueryService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(provider=MockLLM()),
    )

    pipeline_result = await service.execute_query(
        QueryRequest(query="What is this document about?")
    )
    response = to_query_response(pipeline_result)

    assert response.answer
    assert response.confidence == pytest.approx(0.88)
    assert response.chunk_count == 1
    assert len(response.retrieved_chunks) == 1


@pytest.mark.asyncio
async def test_query_pipeline_surfaces_generation_failure_with_retrieved_chunks(
    retrieval_service: AsyncMock,
) -> None:
    llm_service = AsyncMock()
    llm_service.generate_answer.return_value = LLMGenerationResult(
        answer="",
        confidence=0.0,
        success=False,
        provider="mock",
        metadata={"error": "provider unavailable"},
    )
    service = QueryService(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
    )

    result = await service.execute_query(
        QueryRequest(query="What is this document about?")
    )

    assert result.status == "generation_failed"
    assert result.chunk_count == 1
    assert result.answer == ""
    assert result.error is not None
    assert result.error.code is QueryPipelineErrorCode.GENERATION_FAILED
