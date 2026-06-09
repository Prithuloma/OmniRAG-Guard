from __future__ import annotations

import logging
from app.services.llm.base_llm import BaseLLM
from app.services.llm.context_assembler import assemble_context
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult
from app.services.llm.mock_llm import MockLLM
from app.services.retrieval_service import RetrievedChunk

logger = logging.getLogger(__name__)


class LLMService:
    """Orchestrates context assembly and provider-backed answer generation."""

    def __init__(self, *, provider: BaseLLM | None = None) -> None:
        self._provider = provider or MockLLM()

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
            else:
                logger.warning(f"LLM answer generation reported failure: provider={self.provider_name}, error={result.metadata.get('error')}")
            return result
        except Exception as exc:
            logger.error(f"LLM answer generation failed: provider={self.provider_name}, error={exc}")
            return LLMGenerationResult(
                answer="",
                confidence=0.0,
                success=False,
                provider=self._provider.provider_name,
                metadata={"error": str(exc)},
            )


def _map_retrieved_chunk(chunk: RetrievedChunk) -> LLMContextChunk:
    return LLMContextChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        page_number=chunk.page_number,
        text=chunk.text,
        score=chunk.score,
    )
