"""
query_service.py
----------------
Service layer for the query pipeline — validates input, delegates retrieval,
calls LLM generation, verifies evidence, and maps results to API response models.
"""

from __future__ import annotations

import time
from uuid import uuid4

from app.models.base import QueryStatus
from app.models.request_models import QueryRequest
from app.models.response_models import QueryResponse, RetrievedChunk as ApiRetrievedChunk, Citation, RetrievalStats
from app.services.llm.llm_service import LLMService
from app.services.orchestration.orchestration_service import OrchestrationService
from app.services.orchestration.workflow_models import (
    QueryPipelineError,
    QueryPipelineErrorCode,
    QueryPipelineResult,
)
from app.services.retrieval_service import (
    RetrievalService,
    RetrievedChunk,
)
from app.services.verification.verification_service import VerificationService


class QueryService:
    def __init__(
        self,
        *,
        retrieval_service: RetrievalService | None = None,
        llm_service: LLMService | None = None,
        verification_service: VerificationService | None = None,
        orchestration_service: OrchestrationService | None = None,
    ) -> None:
        self._retrieval = retrieval_service or RetrievalService()
        self._llm = llm_service or LLMService()
        self._verification = verification_service or VerificationService()
        self._orchestrator = orchestration_service or OrchestrationService(
            retrieval_service=self._retrieval,
            llm_service=self._llm,
            verification_service=self._verification,
        )

    async def execute_query(self, request: QueryRequest) -> QueryPipelineResult:
        started_at = time.perf_counter()
        query_id = f"qry_{uuid4().hex[:12]}"

        state = await self._orchestrator.run(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
        )

        elapsed_ms = (time.perf_counter() - started_at) * 1000.0

        status = state.execution_metadata.get("status", "failed")
        error = state.execution_metadata.get("error")

        api_chunks = [_map_chunk(chunk) for chunk in state.retrieved_chunks]

        evidence_score = 0.0
        grounding_score = 0.0
        citations = []
        grounded = False
        verification_reason = ""
        if state.verification_result:
            evidence_score = state.verification_result.evidence_score
            grounding_score = getattr(state.verification_result, "grounding_score", 0.0)
            citations = getattr(state.verification_result, "citations", [])
            grounded = state.verification_result.grounded
            verification_reason = state.verification_result.verification_reason

        retrieval_stats = state.execution_metadata.get("retrieval_stats")

        return QueryPipelineResult(
            query_id=query_id,
            query=state.query,
            status=status,
            retrieved_chunks=api_chunks,
            chunk_count=len(api_chunks),
            latency_ms=elapsed_ms,
            answer=state.generated_answer,
            confidence=state.final_confidence,
            evidence_score=evidence_score,
            grounding_score=grounding_score,
            citations=citations,
            retrieval_stats=retrieval_stats,
            grounded=grounded,
            verification_reason=verification_reason,
            error=error,
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

    return QueryResponse(
        success=success,
        message=message,
        query_id=result.query_id,
        query=result.query,
        status=status,
        retrieved_chunks=result.retrieved_chunks,
        chunk_count=result.chunk_count,
        latency_ms=result.latency_ms,
        answer=result.answer,
        confidence=result.confidence,
        evidence_score=result.evidence_score,
        grounding_score=result.grounding_score,
        citations=[Citation(**c) for c in result.citations] if result.citations else [],
        retrieval_stats=RetrievalStats(**result.retrieval_stats) if result.retrieval_stats else None,
        grounded=result.grounded,
        verification_reason=result.verification_reason,
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
        return (
            f"Retrieved {result.chunk_count} chunk(s), generated an answer, "
            "and completed verification."
        )
    if result.error is not None:
        return result.error.message
    return "Query completed."
