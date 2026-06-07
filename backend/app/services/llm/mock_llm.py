from __future__ import annotations

from app.services.llm.base_llm import BaseLLM
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult


def _compute_confidence(chunks: list[LLMContextChunk]) -> float:
    if not chunks:
        return 0.0
    return sum(chunk.score for chunk in chunks) / len(chunks)


def _extract_lead_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    for separator in (". ", "? ", "! ", "\n"):
        if separator in stripped:
            return stripped.split(separator, maxsplit=1)[0].strip()

    return stripped


class MockLLM(BaseLLM):
    """Deterministic LLM stub for development and tests."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        *,
        query: str,
        context: str,
        chunks: list[LLMContextChunk],
    ) -> LLMGenerationResult:
        _ = context

        if not chunks:
            return LLMGenerationResult(
                answer="I could not find enough information to answer that question.",
                confidence=0.0,
                success=True,
                provider=self.provider_name,
                metadata={"strategy": "no_context"},
            )

        lead_sentence = _extract_lead_sentence(chunks[0].text)
        if lead_sentence:
            answer = (
                f"Based on the retrieved documents, {lead_sentence}. "
                f"This addresses the question: {query.strip()}"
            )
        else:
            answer = (
                "Based on the retrieved documents, the available context does not "
                f"contain a clear answer to: {query.strip()}"
            )

        return LLMGenerationResult(
            answer=answer,
            confidence=_compute_confidence(chunks),
            success=True,
            provider=self.provider_name,
            metadata={
                "strategy": "template_summary",
                "chunk_count": len(chunks),
            },
        )
