"""
tests/test_query_pipeline.py
----------------------------
Unit tests for the query pipeline and response mapping.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.base import QueryStatus
from app.models.request_models import QueryRequest
from app.models.response_models import QueryResponse
from app.services.llm.llm_service import LLMService
from app.services.llm.mock_llm import MockLLM
from app.services.query_service import (
    QueryPipelineErrorCode,
    QueryPipelineResult,
    QueryService,
    _map_chunk,
    to_query_response,
)
from app.services.retrieval_service import (
    RetrievalError,
    RetrievalErrorCode,
    RetrievalResult,
    RetrievedChunk,
)


def _success_retrieval_result(*, query: str) -> RetrievalResult:
    return RetrievalResult(
        query=query,
        status="success",
        chunks=[
            RetrievedChunk(
                chunk_id="doc-1:chunk:0",
                document_id="doc-1",
                page_number=2,
                text="Revenue increased by 18% YoY.",
                score=0.91,
            )
        ],
    )


@pytest.fixture
def retrieval_service() -> AsyncMock:
    service = AsyncMock()
    service.retrieve.return_value = _success_retrieval_result(
        query="What drove revenue growth?"
    )
    return service


@pytest.fixture
def query_service(retrieval_service: AsyncMock) -> QueryService:
    return QueryService(
        retrieval_service=retrieval_service,
        llm_service=LLMService(provider=MockLLM()),
    )


@pytest.mark.asyncio
async def test_successful_retrieval(
    query_service: QueryService,
    retrieval_service: AsyncMock,
) -> None:
    request = QueryRequest(query="What drove revenue growth?", top_k=3)

    result = await query_service.execute_query(request)

    assert result.status == "success"
    assert result.error is None
    assert result.query == "What drove revenue growth?"
    assert result.chunk_count == 1
    assert len(result.retrieved_chunks) == 1
    assert result.retrieved_chunks[0].text == "Revenue increased by 18% YoY."
    assert result.answer
    assert "Revenue increased by 18% YoY" in result.answer
    assert result.confidence == pytest.approx(0.91)
    assert result.latency_ms >= 0.0
    retrieval_service.retrieve.assert_awaited_once_with(
        "What drove revenue growth?",
        top_k=3,
    )


@pytest.mark.asyncio
async def test_empty_query_rejection(query_service: QueryService) -> None:
    request = QueryRequest(query="   ")

    result = await query_service.execute_query(request)

    assert result.status == "empty_query"
    assert result.chunk_count == 0
    assert result.retrieved_chunks == []
    assert result.error is not None
    assert result.error.code is QueryPipelineErrorCode.EMPTY_QUERY


@pytest.mark.asyncio
async def test_no_results_response(retrieval_service: AsyncMock) -> None:
    retrieval_service.retrieve.return_value = RetrievalResult(
        query="unknown topic",
        status="no_results",
        chunks=[],
        error=RetrievalError(
            code=RetrievalErrorCode.NO_RESULTS,
            message="No matching chunks found for query.",
        ),
    )
    service = QueryService(retrieval_service=retrieval_service)

    result = await service.execute_query(QueryRequest(query="unknown topic"))

    assert result.status == "no_results"
    assert result.chunk_count == 0
    assert result.retrieved_chunks == []
    assert result.error is not None
    assert result.error.code is QueryPipelineErrorCode.NO_RESULTS


@pytest.mark.asyncio
async def test_retrieval_service_failure(retrieval_service: AsyncMock) -> None:
    retrieval_service.retrieve.return_value = RetrievalResult(
        query="revenue growth",
        status="embedding_failed",
        chunks=[],
        error=RetrievalError(
            code=RetrievalErrorCode.EMBEDDING_FAILED,
            message="Failed to generate query embedding.",
            detail="backend unavailable",
        ),
    )
    service = QueryService(retrieval_service=retrieval_service)

    result = await service.execute_query(QueryRequest(query="revenue growth"))

    assert result.status == "retrieval_failed"
    assert result.chunk_count == 0
    assert result.error is not None
    assert result.error.code is QueryPipelineErrorCode.RETRIEVAL_FAILED


@pytest.mark.asyncio
async def test_qdrant_unavailable_failure(retrieval_service: AsyncMock) -> None:
    retrieval_service.retrieve.return_value = RetrievalResult(
        query="revenue growth",
        status="qdrant_unavailable",
        chunks=[],
        error=RetrievalError(
            code=RetrievalErrorCode.QDRANT_UNAVAILABLE,
            message="Qdrant vector search is unavailable.",
            detail="connection refused",
        ),
    )
    service = QueryService(retrieval_service=retrieval_service)

    result = await service.execute_query(QueryRequest(query="revenue growth"))

    assert result.status == "qdrant_unavailable"
    assert result.error is not None
    assert result.error.code is QueryPipelineErrorCode.QDRANT_UNAVAILABLE


def test_response_schema_correctness() -> None:
    chunk = RetrievedChunk(
        chunk_id="doc-1:chunk:0",
        document_id="doc-1",
        page_number=2,
        text="Revenue increased by 18% YoY.",
        score=0.91,
    )
    result = QueryPipelineResult(
        query_id="qry_test123",
        query="What drove revenue growth?",
        status="success",
        retrieved_chunks=[_map_chunk(chunk)],
        chunk_count=1,
        latency_ms=12.5,
        answer="Generated answer.",
        confidence=0.91,
    )

    response = to_query_response(result)
    payload = response.model_dump()

    assert set(payload.keys()) >= {
        "success",
        "message",
        "timestamp",
        "query_id",
        "query",
        "status",
        "retrieved_chunks",
        "chunk_count",
        "latency_ms",
    }
    assert payload["query_id"] == "qry_test123"
    assert payload["query"] == "What drove revenue growth?"
    assert payload["status"] == QueryStatus.SUCCESS.value
    assert payload["chunk_count"] == 1
    assert payload["latency_ms"] == 12.5
    assert len(payload["retrieved_chunks"]) == 1
    assert payload["retrieved_chunks"][0]["chunk_id"] == "doc-1:chunk:0"
    assert payload["retrieved_chunks"][0]["document_id"] == "doc-1"
    assert payload["retrieved_chunks"][0]["page_number"] == 2
    assert payload["retrieved_chunks"][0]["text"] == "Revenue increased by 18% YoY."
    assert payload["retrieved_chunks"][0]["score"] == 0.91
    assert payload["answer"] == "Generated answer."
    assert payload["confidence"] == 0.91

    validated = QueryResponse.model_validate(payload)
    assert validated.status is QueryStatus.SUCCESS


def test_response_accepts_negative_qdrant_scores() -> None:
    negative_score = -0.0054543726
    chunk = RetrievedChunk(
        chunk_id="doc-1:chunk:0",
        document_id="doc-1",
        page_number=1,
        text="Chunk with negative similarity score.",
        score=negative_score,
    )
    result = QueryPipelineResult(
        query_id="qry_negative_score",
        query="test query",
        status="success",
        retrieved_chunks=[_map_chunk(chunk)],
        chunk_count=1,
        latency_ms=3.2,
        answer="Answer grounded in negative-score chunk.",
        confidence=negative_score,
    )

    response = to_query_response(result)

    assert response.retrieved_chunks[0].score == negative_score
    assert response.confidence == negative_score
    assert response.answer == "Answer grounded in negative-score chunk."
    QueryResponse.model_validate(response.model_dump())
