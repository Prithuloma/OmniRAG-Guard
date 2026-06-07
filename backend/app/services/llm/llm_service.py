from __future__ import annotations

from app.services.llm.base_llm import BaseLLM
from app.services.llm.context_assembler import assemble_context
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult
from app.services.llm.mock_llm import MockLLM
from app.services.retrieval_service import RetrievedChunk


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
        llm_chunks = [_map_retrieved_chunk(chunk) for chunk in chunks]
        context = assemble_context(llm_chunks)

        try:
            return await self._provider.generate(
                query=query,
                context=context,
                chunks=llm_chunks,
            )
        except Exception as exc:
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
