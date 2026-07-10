from __future__ import annotations

import logging
from app.core.config import settings
from app.services.llm.base_llm import BaseLLM
from app.services.llm.context_assembler import assemble_context
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult
from app.services.llm.mock_llm import MockLLM
from app.services.retrieval_service import RetrievedChunk

logger = logging.getLogger(__name__)


class LLMService:
    """Orchestrates context assembly and provider-backed answer generation."""

    def __init__(self, *, provider: BaseLLM | None = None) -> None:
        if provider is not None:
            self._provider = provider
        else:
            provider_setting = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "mock"
            if provider_setting == "gemini":
                if settings.GEMINI_API_KEY:
                    from app.services.llm.gemini_llm import GeminiLLM
                    self._provider = GeminiLLM()
                else:
                    logger.warning("LLM_PROVIDER is configured as 'gemini' but GEMINI_API_KEY is missing. Falling back to MockLLM.")
                    self._provider = MockLLM()
            else:
                self._provider = MockLLM()

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    async def generate_answer(
        self,
        *,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> LLMGenerationResult:
        logger.info(f"LLM answer generation requested: query='{query}', context_chunks={len(chunks)}")
        llm_chunks = [_map_retrieved_chunk(chunk) for chunk in chunks]
        context = assemble_context(llm_chunks)

        try:
            result = await self._provider.generate(
                query=query,
                context=context,
                chunks=llm_chunks,
            )
            if result.success:
                logger.info(f"LLM answer generation succeeded: provider={self.provider_name}, answer_length={len(result.answer)}")
                return result
            else:
                if self._provider.provider_name == "gemini":
                    logger.warning(f"Gemini provider reported failure, attempting query-time fallback to MockLLM. Error: {result.metadata.get('error')}")
                    return await self._fallback_generate(query, context, llm_chunks, warning=f"Gemini reported failure: {result.metadata.get('error')}")
                return result
        except Exception as exc:
            logger.error(f"LLM answer generation failed: provider={self.provider_name}, error={exc}")
            if self._provider.provider_name == "gemini":
                logger.info("Attempting query-time fallback to MockLLM due to exception.")
                return await self._fallback_generate(query, context, llm_chunks, warning=str(exc))
            return LLMGenerationResult(
                answer="",
                confidence=0.0,
                success=False,
                provider=self._provider.provider_name,
                metadata={"error": str(exc)},
            )

    async def _fallback_generate(
        self,
        query: str,
        context: str,
        chunks: list[LLMContextChunk],
        warning: str,
    ) -> LLMGenerationResult:
        fallback_provider = MockLLM()
        result = await fallback_provider.generate(
            query=query,
            context=context,
            chunks=chunks,
        )
        updated_metadata = dict(result.metadata)
        updated_metadata["fallback_warning"] = warning
        updated_metadata["original_provider"] = "gemini"
        
        return LLMGenerationResult(
            answer=result.answer,
            confidence=result.confidence,
            success=result.success,
            provider=result.provider,
            metadata=updated_metadata,
        )


def _map_retrieved_chunk(chunk: RetrievedChunk) -> LLMContextChunk:
    return LLMContextChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        page_number=chunk.page_number,
        text=chunk.text,
        score=chunk.score,
    )

