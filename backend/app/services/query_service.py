"""
query_service.py
----------------
Service layer for the query pipeline — validates input, delegates retrieval,
and maps results to API response models.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from app.models.base import QueryStatus
from app.models.request_models import QueryRequest
from app.models.response_models import QueryResponse, RetrievedChunk as ApiRetrievedChunk
from app.services.retrieval_service import (
    RetrievalService,
    RetrievedChunk,
)


class QueryPipelineErrorCode(str, Enum):
    EMPTY_QUERY = "EMPTY_QUERY"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    QDRANT_UNAVAILABLE = "QDRANT_UNAVAILABLE"
    NO_RESULTS = "NO_RESULTS"


@dataclass(frozen=True, slots=True)
class QueryPipelineError:
    code: QueryPipelineErrorCode
    message: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class QueryPipelineResult:
    query_id: str
    query: str
    status: str
    retrieved_chunks: list[ApiRetrievedChunk]
    chunk_count: int
    latency_ms: float
    error: QueryPipelineError | None = None


class QueryService:
    def __init__(self, *, retrieval_service: RetrievalService | None = None) -> None:
        self._retrieval = retrieval_service or RetrievalService()

    async def execute_query(self, request: QueryRequest) -> QueryPipelineResult:
        started_at = time.perf_counter()
        query_id = f"qry_{uuid4().hex[:12]}"
        normalized_query = request.query.strip()

        if not normalized_query:
            return self._error_result(
                query_id=query_id,
                query=request.query,
                status="empty_query",
                started_at=started_at,
                error=QueryPipelineError(
                    code=QueryPipelineErrorCode.EMPTY_QUERY,
                    message="Query must not be empty.",
                ),
            )

        retrieval_result = await self._retrieval.retrieve(
            normalized_query,
            top_k=request.top_k,
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0

        if retrieval_result.status == "success":
            api_chunks = [_map_chunk(chunk) for chunk in retrieval_result.chunks]
            return QueryPipelineResult(
                query_id=query_id,
                query=retrieval_result.query,
                status="success",
                retrieved_chunks=api_chunks,
                chunk_count=len(api_chunks),
                latency_ms=elapsed_ms,
            )

        if retrieval_result.status == "no_results":
            return QueryPipelineResult(
                query_id=query_id,
                query=retrieval_result.query,
                status="no_results",
                retrieved_chunks=[],
                chunk_count=0,
                latency_ms=elapsed_ms,
                error=QueryPipelineError(
                    code=QueryPipelineErrorCode.NO_RESULTS,
                    message=retrieval_result.error.message if retrieval_result.error else "No results.",
                    detail=retrieval_result.error.detail if retrieval_result.error else None,
                ),
            )

        if retrieval_result.status == "qdrant_unavailable":
            return QueryPipelineResult(
                query_id=query_id,
                query=retrieval_result.query,
                status="qdrant_unavailable",
                retrieved_chunks=[],
                chunk_count=0,
                latency_ms=elapsed_ms,
                error=QueryPipelineError(
                    code=QueryPipelineErrorCode.QDRANT_UNAVAILABLE,
                    message=(
                        retrieval_result.error.message
                        if retrieval_result.error
                        else "Qdrant vector search is unavailable."
                    ),
                    detail=retrieval_result.error.detail if retrieval_result.error else None,
                ),
            )

        retrieval_error = retrieval_result.error
        return QueryPipelineResult(
            query_id=query_id,
            query=retrieval_result.query,
            status="retrieval_failed",
            retrieved_chunks=[],
            chunk_count=0,
            latency_ms=elapsed_ms,
            error=QueryPipelineError(
                code=QueryPipelineErrorCode.RETRIEVAL_FAILED,
                message=(
                    retrieval_error.message
                    if retrieval_error
                    else "Retrieval failed."
                ),
                detail=retrieval_error.detail if retrieval_error else None,
            ),
        )

    @staticmethod
    def _error_result(
        *,
        query_id: str,
        query: str,
        status: str,
        started_at: float,
        error: QueryPipelineError,
    ) -> QueryPipelineResult:
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        return QueryPipelineResult(
            query_id=query_id,
            query=query,
            status=status,
            retrieved_chunks=[],
            chunk_count=0,
            latency_ms=elapsed_ms,
            error=error,
        )


def to_query_response(result: QueryPipelineResult) -> QueryResponse:
    """Map a pipeline result to the public API response model."""
    status = _map_query_status(result.status)
    success = result.status in {"success", "no_results"}
    message = _result_message(result)

    confidence = 0.0
    if result.retrieved_chunks:
        confidence = max(chunk.score for chunk in result.retrieved_chunks)

    return QueryResponse(
        success=success,
        message=message,
        query_id=result.query_id,
        query=result.query,
        status=status,
        retrieved_chunks=result.retrieved_chunks,
        chunk_count=result.chunk_count,
        latency_ms=result.latency_ms,
        answer="",
        confidence=confidence,
    )


def _map_chunk(chunk: RetrievedChunk) -> ApiRetrievedChunk:
    return ApiRetrievedChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        page_number=chunk.page_number,
        text=chunk.text,
        score=chunk.score,
    )


def _map_query_status(status: str) -> QueryStatus:
    if status == "success":
        return QueryStatus.SUCCESS
    if status == "no_results":
        return QueryStatus.NO_RESULTS
    return QueryStatus.FAILED


def _result_message(result: QueryPipelineResult) -> str:
    if result.status == "success":
        return f"Retrieved {result.chunk_count} chunk(s)."
    if result.error is not None:
        return result.error.message
    return "Query completed."
