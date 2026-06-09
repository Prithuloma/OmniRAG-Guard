from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.services.orchestration.orchestration_service import OrchestrationService
from app.services.orchestration.workflow_models import (
    QueryPipelineError,
    QueryPipelineErrorCode,
)
from app.services.orchestration.workflow_state import WorkflowState
from app.services.retrieval_service import (
    RetrievalError,
    RetrievalErrorCode,
    RetrievalResult,
    RetrievedChunk,
)
from app.services.llm.llm_models import LLMGenerationResult
from app.services.verification.verification_models import VerificationResult


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_retrieved_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id="doc-1:chunk:0",
            document_id="doc-1",
            page_number=1,
            text="OmniRAG-Guard uses an Orchestration Layer.",
            score=0.95,
        )
    ]


@pytest.fixture
def retrieval_service(mock_retrieved_chunks: list[RetrievedChunk]) -> AsyncMock:
    service = AsyncMock()
    service.retrieve.return_value = RetrievalResult(
        query="What is OmniRAG-Guard?",
        status="success",
        chunks=mock_retrieved_chunks,
    )
    return service


@pytest.fixture
def llm_service() -> AsyncMock:
    service = AsyncMock()
    service.generate_answer.return_value = LLMGenerationResult(
        answer="OmniRAG-Guard uses an Orchestration Layer.",
        confidence=0.90,
        success=True,
    )
    return service


@pytest.fixture
def verification_service() -> AsyncMock:
    service = AsyncMock()
    service.verify.return_value = VerificationResult(
        evidence_score=0.95,
        grounded=True,
        verification_reason="Answer is supported by retrieved chunks.",
        confidence=0.93,
        retrieval_confidence=0.95,
    )
    return service


@pytest.fixture
def orchestrator(
    retrieval_service: AsyncMock,
    llm_service: AsyncMock,
    verification_service: AsyncMock,
) -> OrchestrationService:
    return OrchestrationService(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
        verification_service=verification_service,
    )


# ── Unit Tests for Steps ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retrieve_step_success(
    orchestrator: OrchestrationService,
    retrieval_service: AsyncMock,
    mock_retrieved_chunks: list[RetrievedChunk],
) -> None:
    state = WorkflowState(query="What is OmniRAG-Guard?")
    updated_state = await orchestrator.retrieve_step(state)

    assert updated_state.execution_metadata["status"] == "success"
    assert updated_state.retrieved_chunks == mock_retrieved_chunks
    assert "error" not in updated_state.execution_metadata
    retrieval_service.retrieve.assert_awaited_once_with("What is OmniRAG-Guard?", top_k=5, filters=None)


@pytest.mark.asyncio
async def test_retrieve_step_empty_query(orchestrator: OrchestrationService) -> None:
    state = WorkflowState(query="   ")
    updated_state = await orchestrator.retrieve_step(state)

    assert updated_state.execution_metadata["status"] == "empty_query"
    assert updated_state.execution_metadata["error"].code == QueryPipelineErrorCode.EMPTY_QUERY
    assert not updated_state.retrieved_chunks


@pytest.mark.asyncio
async def test_retrieve_step_failure(
    orchestrator: OrchestrationService,
    retrieval_service: AsyncMock,
) -> None:
    retrieval_service.retrieve.return_value = RetrievalResult(
        query="error query",
        status="embedding_failed",
        chunks=[],
        error=RetrievalError(
            code=RetrievalErrorCode.EMBEDDING_FAILED,
            message="Failed to generate query embedding.",
        ),
    )
    state = WorkflowState(query="error query")
    updated_state = await orchestrator.retrieve_step(state)

    assert updated_state.execution_metadata["status"] == "retrieval_failed"
    assert updated_state.execution_metadata["error"].code == QueryPipelineErrorCode.RETRIEVAL_FAILED
    assert not updated_state.retrieved_chunks


@pytest.mark.asyncio
async def test_generate_step_success(
    orchestrator: OrchestrationService,
    llm_service: AsyncMock,
    mock_retrieved_chunks: list[RetrievedChunk],
) -> None:
    state = WorkflowState(query="What is OmniRAG-Guard?")
    state.retrieved_chunks = mock_retrieved_chunks
    state.execution_metadata["status"] = "success"

    updated_state = await orchestrator.generate_step(state)

    assert updated_state.generated_answer == "OmniRAG-Guard uses an Orchestration Layer."
    assert "error" not in updated_state.execution_metadata
    llm_service.generate_answer.assert_awaited_once_with(
        query="What is OmniRAG-Guard?",
        chunks=mock_retrieved_chunks,
    )


@pytest.mark.asyncio
async def test_generate_step_failure(
    orchestrator: OrchestrationService,
    llm_service: AsyncMock,
    mock_retrieved_chunks: list[RetrievedChunk],
) -> None:
    llm_service.generate_answer.return_value = LLMGenerationResult(
        answer="",
        confidence=0.0,
        success=False,
        metadata={"error": "provider timeout"},
    )
    state = WorkflowState(query="What is OmniRAG-Guard?")
    state.retrieved_chunks = mock_retrieved_chunks
    state.execution_metadata["status"] = "success"

    updated_state = await orchestrator.generate_step(state)

    assert updated_state.generated_answer == ""
    assert updated_state.execution_metadata["status"] == "generation_failed"
    assert updated_state.execution_metadata["error"].code == QueryPipelineErrorCode.GENERATION_FAILED
    assert updated_state.execution_metadata["error"].detail == "provider timeout"


@pytest.mark.asyncio
async def test_verify_step_success(
    orchestrator: OrchestrationService,
    verification_service: AsyncMock,
    mock_retrieved_chunks: list[RetrievedChunk],
) -> None:
    state = WorkflowState(query="What is OmniRAG-Guard?")
    state.retrieved_chunks = mock_retrieved_chunks
    state.generated_answer = "OmniRAG-Guard uses an Orchestration Layer."
    state.execution_metadata["status"] = "success"

    updated_state = await orchestrator.verify_step(state)

    assert updated_state.verification_result is not None
    assert updated_state.verification_result.grounded is True
    assert updated_state.final_confidence == 0.93
    verification_service.verify.assert_awaited_once_with(
        query="What is OmniRAG-Guard?",
        generated_answer="OmniRAG-Guard uses an Orchestration Layer.",
        retrieved_chunks=mock_retrieved_chunks,
    )


# ── Integration & Error Handling Flow Tests ───────────────────────────────

@pytest.mark.asyncio
async def test_full_pipeline_success(
    orchestrator: OrchestrationService,
    mock_retrieved_chunks: list[RetrievedChunk],
) -> None:
    state = await orchestrator.run("What is OmniRAG-Guard?", top_k=5)

    assert state.execution_metadata["status"] == "success"
    assert state.retrieved_chunks == mock_retrieved_chunks
    assert state.generated_answer == "OmniRAG-Guard uses an Orchestration Layer."
    assert state.final_confidence == 0.93
    assert state.execution_metadata["latency_ms"] >= 0.0
    assert "error" not in state.execution_metadata


@pytest.mark.asyncio
async def test_pipeline_skips_subsequent_steps_on_failure(
    orchestrator: OrchestrationService,
    retrieval_service: AsyncMock,
    llm_service: AsyncMock,
    verification_service: AsyncMock,
) -> None:
    # Set retrieval status to "no_results"
    retrieval_service.retrieve.return_value = RetrievalResult(
        query="unresolved query",
        status="no_results",
        chunks=[],
        error=RetrievalError(
            code=RetrievalErrorCode.NO_RESULTS,
            message="No matching chunks found for query.",
        ),
    )

    state = await orchestrator.run("unresolved query")

    # Assert status is set to no_results
    assert state.execution_metadata["status"] == "no_results"
    assert state.execution_metadata["error"].code == QueryPipelineErrorCode.NO_RESULTS
    
    # Assert other fields are default/empty
    assert not state.retrieved_chunks
    assert state.generated_answer == ""
    assert state.verification_result is None

    # Assert that LLM generation and Verification services were NEVER called
    llm_service.generate_answer.assert_not_awaited()
    verification_service.verify.assert_not_awaited()
