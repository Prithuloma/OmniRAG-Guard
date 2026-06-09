from __future__ import annotations

import time
from typing import Any, Optional

from app.models.request_models import QueryFilters
from app.services.llm.llm_service import LLMService
from app.services.orchestration.workflow_models import (
    QueryPipelineError,
    QueryPipelineErrorCode,
)
from app.services.orchestration.workflow_state import WorkflowState
from app.services.retrieval_service import RetrievalService
from app.services.verification.verification_service import VerificationService


class OrchestrationService:
    """
    OrchestrationService coordinates the pipeline execution by passing a WorkflowState
    through a sequence of node-like processing steps (retrieve, generate, verify).
    """

    def __init__(
        self,
        *,
        retrieval_service: RetrievalService | None = None,
        llm_service: LLMService | None = None,
        verification_service: VerificationService | None = None,
    ) -> None:
        self._retrieval = retrieval_service or RetrievalService()
        self._llm = llm_service or LLMService()
        self._verification = verification_service or VerificationService()

    async def retrieve_step(self, state: WorkflowState, top_k: int = 5) -> WorkflowState:
        """
        Retrieval step. Executes document retrieval and transitions the state.
        Designed as a separable workflow node.
        """
        if "error" in state.execution_metadata:
            return state

        normalized_query = state.query.strip()
        if not normalized_query:
            state.execution_metadata["status"] = "empty_query"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.EMPTY_QUERY,
                message="Query must not be empty.",
            )
            return state

        try:
            retrieval_result = await self._retrieval.retrieve(
                normalized_query,
                top_k=top_k,
                filters=state.filters,
            )
        except Exception as exc:
            state.execution_metadata["status"] = "retrieval_failed"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.RETRIEVAL_FAILED,
                message="Retrieval failed.",
                detail=str(exc),
            )
            return state

        # Collect search metrics
        state.execution_metadata["retrieval_stats"] = {
            "chunks_retrieved": len(retrieval_result.chunks),
            "search_time_ms": getattr(retrieval_result, "search_time_ms", 0.0),
            "rerank_time_ms": getattr(retrieval_result, "rerank_time_ms", 0.0),
        }

        if retrieval_result.status == "success":
            state.retrieved_chunks = retrieval_result.chunks
            state.execution_metadata["status"] = "success"
        elif retrieval_result.status == "no_results":
            state.execution_metadata["status"] = "no_results"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.NO_RESULTS,
                message=retrieval_result.error.message if retrieval_result.error else "No results.",
                detail=retrieval_result.error.detail if retrieval_result.error else None,
            )
        elif retrieval_result.status == "qdrant_unavailable":
            state.execution_metadata["status"] = "qdrant_unavailable"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.QDRANT_UNAVAILABLE,
                message=(
                    retrieval_result.error.message
                    if retrieval_result.error
                    else "Qdrant vector search is unavailable."
                ),
                detail=retrieval_result.error.detail if retrieval_result.error else None,
            )
        else:
            state.execution_metadata["status"] = "retrieval_failed"
            retrieval_error = retrieval_result.error
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.RETRIEVAL_FAILED,
                message=(
                    retrieval_error.message
                    if retrieval_error
                    else "Retrieval failed."
                ),
                detail=retrieval_error.detail if retrieval_error else None,
            )

        return state

    async def generate_step(self, state: WorkflowState) -> WorkflowState:
        """
        Generation step. Assembles context, generates an answer, and transitions the state.
        Designed as a separable workflow node.
        """
        if state.execution_metadata.get("status") != "success" or "error" in state.execution_metadata:
            return state

        try:
            generation = await self._llm.generate_answer(
                query=state.query,
                chunks=state.retrieved_chunks,
            )
        except Exception as exc:
            state.execution_metadata["status"] = "generation_failed"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.GENERATION_FAILED,
                message="Failed to generate an answer from retrieved context.",
                detail=str(exc),
            )
            return state

        if not generation.success or not generation.answer.strip():
            state.execution_metadata["status"] = "generation_failed"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.GENERATION_FAILED,
                message="Failed to generate an answer from retrieved context.",
                detail=generation.metadata.get("error"),
            )
        else:
            state.generated_answer = generation.answer

        return state

    async def verify_step(self, state: WorkflowState) -> WorkflowState:
        """
        Verification step. Validates groundedness and updates the state.
        Designed as a separable workflow node.
        """
        if state.execution_metadata.get("status") != "success" or "error" in state.execution_metadata:
            return state

        try:
            verification = await self._verification.verify(
                query=state.query,
                generated_answer=state.generated_answer,
                retrieved_chunks=state.retrieved_chunks,
            )
            state.verification_result = verification
            state.final_confidence = verification.confidence
            state.execution_metadata["status"] = "success"
        except Exception as exc:
            state.execution_metadata["status"] = "failed"
            state.execution_metadata["error"] = QueryPipelineError(
                code=QueryPipelineErrorCode.RETRIEVAL_FAILED,
                message="Verification failed.",
                detail=str(exc),
            )

        return state

    async def run(
        self,
        query: str,
        top_k: int = 5,
        filters: QueryFilters | None = None,
    ) -> WorkflowState:
        """
        Executes the entire sequential pipeline by passing the WorkflowState
        through the nodes retrieve_step, generate_step, and verify_step.
        """
        state = WorkflowState(query=query, filters=filters)
        state.execution_metadata["started_at"] = time.perf_counter()

        # Step 1: Retrieval
        state = await self.retrieve_step(state, top_k=top_k)

        # Step 2: Generation
        state = await self.generate_step(state)

        # Step 3: Verification
        state = await self.verify_step(state)

        # Final latency calculation
        started_at = state.execution_metadata.get("started_at")
        if started_at is not None:
            state.execution_metadata["latency_ms"] = (time.perf_counter() - started_at) * 1000.0

        return state
