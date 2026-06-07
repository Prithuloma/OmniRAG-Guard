"""
tests/test_llm_service.py
-------------------------
Unit tests for LLM answer generation layer.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.services.llm.context_assembler import assemble_context
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult
from app.services.llm.llm_service import LLMService
from app.services.llm.mock_llm import MockLLM
from app.services.retrieval_service import RetrievedChunk


def _make_chunk(*, text: str, score: float = 0.91) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="doc-1:chunk:0",
        document_id="doc-1",
        page_number=2,
        text=text,
        score=score,
    )


def test_assemble_context_includes_metadata_and_text() -> None:
    chunks = [
        LLMContextChunk(
            chunk_id="doc-1:chunk:0",
            document_id="doc-1",
            page_number=2,
            text="Revenue increased by 18% YoY.",
            score=0.91,
        ),
        LLMContextChunk(
            chunk_id="doc-1:chunk:1",
            document_id="doc-1",
            page_number=3,
            text="SaaS subscriptions drove growth.",
            score=0.84,
        ),
    ]

    context = assemble_context(chunks)

    assert "document_id=doc-1" in context
    assert "Revenue increased by 18% YoY." in context
    assert "SaaS subscriptions drove growth." in context
    assert "[Source 1]" in context
    assert "[Source 2]" in context


@pytest.mark.asyncio
async def test_mock_llm_generates_answer_from_top_chunk() -> None:
    service = LLMService(provider=MockLLM())

    result = await service.generate_answer(
        query="What drove revenue growth?",
        chunks=[_make_chunk(text="Revenue increased by 18% YoY.")],
    )

    assert result.success is True
    assert result.provider == "mock"
    assert "Revenue increased by 18% YoY" in result.answer
    assert "What drove revenue growth?" in result.answer
    assert result.confidence == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_mock_llm_preserves_negative_confidence_scores() -> None:
    service = LLMService(provider=MockLLM())

    result = await service.generate_answer(
        query="What is this document about?",
        chunks=[_make_chunk(text="Microservices architecture overview.", score=-0.0054543726)],
    )

    assert result.confidence == pytest.approx(-0.0054543726)


@pytest.mark.asyncio
async def test_llm_service_handles_provider_failure() -> None:
    provider = AsyncMock()
    provider.provider_name = "failing-provider"
    provider.generate.side_effect = RuntimeError("provider unavailable")
    service = LLMService(provider=provider)

    result = await service.generate_answer(
        query="test query",
        chunks=[_make_chunk(text="Some context.")],
    )

    assert result.success is False
    assert result.answer == ""
    assert result.confidence == 0.0
    assert result.metadata["error"] == "provider unavailable"


@pytest.mark.asyncio
async def test_llm_service_can_use_injected_provider() -> None:
    provider = AsyncMock()
    provider.provider_name = "custom-provider"
    provider.generate.return_value = LLMGenerationResult(
        answer="Custom provider answer.",
        confidence=0.75,
        success=True,
        provider="custom-provider",
    )
    service = LLMService(provider=provider)

    result = await service.generate_answer(
        query="custom query",
        chunks=[_make_chunk(text="Custom context.")],
    )

    assert result.answer == "Custom provider answer."
    assert result.confidence == 0.75
    provider.generate.assert_awaited_once()
