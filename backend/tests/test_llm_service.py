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


@pytest.mark.asyncio
async def test_gemini_llm_generation_success() -> None:
    from unittest.mock import patch, MagicMock
    from app.services.llm.gemini_llm import GeminiLLM

    with patch("app.services.llm.gemini_llm.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_key"
        mock_settings.GEMINI_MODEL = "gemini-1.5-flash"
        
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            mock_response = MagicMock()
            mock_response.text = "This is a real Gemini response."
            mock_model_instance.generate_content_async = AsyncMock(return_value=mock_response)
            
            provider = GeminiLLM()
            chunks = [
                LLMContextChunk(
                    chunk_id="doc-1:chunk:0",
                    document_id="doc-1",
                    page_number=2,
                    text="Revenue increased by 18% YoY.",
                    score=0.91,
                )
            ]
            
            result = await provider.generate(
                query="What drove growth?",
                context="Some context",
                chunks=chunks
            )
            
            assert result.success is True
            assert result.provider == "gemini"
            assert result.answer == "This is a real Gemini response."
            assert result.confidence == 0.91
            assert result.metadata["model"] == "gemini-1.5-flash"
            assert result.metadata["chunk_count"] == 1
            
            mock_model_class.assert_called_with(
                model_name="gemini-1.5-flash",
                system_instruction=(
                    "You are a retrieval-augmented assistant.\n"
                    "Answer the user's question ONLY using the provided retrieved context blocks wrapped in <source_text> tags.\n"
                    "Do not hallucinate or answer from your own knowledge.\n"
                    "If the answer cannot be found in the supplied context, explicitly state: "
                    "\"The uploaded documents do not contain enough information to answer this question.\"\n"
                    "Rely solely on the facts provided in the context. Do not mention or reference any facts not explicitly present in the context."
                )
            )


@pytest.mark.asyncio
async def test_gemini_llm_generation_failure_fallback() -> None:
    from unittest.mock import patch

    with patch("app.services.llm.llm_service.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.GEMINI_API_KEY = "dummy_key"
        mock_settings.GEMINI_MODEL = "gemini-1.5-flash"
        
        with patch("app.services.llm.gemini_llm.GeminiLLM.generate", side_effect=RuntimeError("API quota exceeded")):
            service = LLMService()
            assert service.provider_name == "gemini"
            
            result = await service.generate_answer(
                query="What drove growth?",
                chunks=[_make_chunk(text="Revenue increased by 18% YoY.")],
            )
            
            assert result.success is True
            assert result.provider == "mock"
            assert "Revenue increased by 18% YoY" in result.answer
            assert "What drove growth?" in result.answer
            assert result.metadata["fallback_warning"] == "API quota exceeded"
            assert result.metadata["original_provider"] == "gemini"


def test_settings_dynamic_llm_provider_selection() -> None:
    from unittest.mock import patch

    # 1. Configured as gemini with API key
    with patch("app.services.llm.llm_service.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.GEMINI_API_KEY = "dummy_key"
        
        service = LLMService()
        assert service.provider_name == "gemini"

    # 2. Configured as gemini without API key -> falls back to mock
    with patch("app.services.llm.llm_service.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.GEMINI_API_KEY = None
        
        service = LLMService()
        assert service.provider_name == "mock"

    # 3. Configured as mock -> MockLLM
    with patch("app.services.llm.llm_service.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "mock"
        mock_settings.GEMINI_API_KEY = "dummy_key"
        
        service = LLMService()
        assert service.provider_name == "mock"

