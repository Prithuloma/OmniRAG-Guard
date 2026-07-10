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
            state.execution_metadata["llm_metadata"] = generation.metadata

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

        # Detect document-level summarization queries
        is_summary = False
        q_lower = query.lower().strip()
        summary_keywords = ["summarize", "summary", "overview", "explain this", "key points", "takeaway", "takeaways"]
        if any(k in q_lower for k in summary_keywords):
            is_summary = True
        state.execution_metadata["is_summary"] = is_summary

        # Step 1: Retrieval
        t0 = time.perf_counter()
        actual_top_k = 25 if is_summary else top_k
        state = await self.retrieve_step(state, top_k=actual_top_k)
        state.execution_metadata["retrieval_time_ms"] = (time.perf_counter() - t0) * 1000.0

        # Step 2: Generation
        t1 = time.perf_counter()
        state = await self.generate_step(state)
        state.execution_metadata["generation_time_ms"] = (time.perf_counter() - t1) * 1000.0

        # Step 3: Verification
        t2 = time.perf_counter()
        state = await self.verify_step(state)
        state.execution_metadata["verification_time_ms"] = (time.perf_counter() - t2) * 1000.0

        # Step 4: Self-Correction Refinement Loop
        state.execution_metadata["self_correction_triggered"] = False
        state.execution_metadata["refinement_time_ms"] = 0.0

        import logging
        logger = logging.getLogger(__name__)

        if state.verification_result and (not state.verification_result.grounded or any(c.get("status") == "ungrounded" for c in state.verification_result.claims)):
            ungrounded_claims = [c for c in state.verification_result.claims if c.get("status") == "ungrounded"]
            if ungrounded_claims:
                logger.info(f"Low grounding score or ungrounded claims detected. Triggering self-correction refinement.")
                t_refine_start = time.perf_counter()
                
                refinement_warnings = "\n".join([f"- \"{c.get('text')}\"" for c in ungrounded_claims])
                refine_query = (
                    f"{query}\n\n"
                    f"[REFINEMENT FEEDBACK]\n"
                    f"Your previous response failed verification checks because the following statements are unsupported by the context:\n"
                    f"{refinement_warnings}\n\n"
                    f"Please revise the response. Modify or completely remove these unsupported assertions. Ensure every remaining statement is fully grounded in the retrieved context blocks."
                )
                
                try:
                    generation = await self._llm.generate_answer(
                        query=refine_query,
                        chunks=state.retrieved_chunks,
                    )
                    if generation.success and generation.answer.strip():
                        state.generated_answer = generation.answer
                        state.execution_metadata["llm_metadata"] = generation.metadata
                        state.execution_metadata["self_correction_triggered"] = True
                        
                        # Re-verify the corrected response
                        verification = await self._verification.verify(
                            query=query,
                            generated_answer=state.generated_answer,
                            retrieved_chunks=state.retrieved_chunks,
                        )
                        state.verification_result = verification
                        state.final_confidence = verification.confidence
                except Exception as exc:
                    logger.error(f"Self-correction refinement failed: {exc}")
                
                state.execution_metadata["refinement_time_ms"] = (time.perf_counter() - t_refine_start) * 1000.0

        # Final latency calculation
        started_at = state.execution_metadata.get("started_at")
        if started_at is not None:
            state.execution_metadata["latency_ms"] = (time.perf_counter() - started_at) * 1000.0

        return state
