from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult


class BaseLLM(ABC):
    """Provider interface for answer generation backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a stable provider identifier."""

    @abstractmethod
    async def generate(
        self,
        *,
        query: str,
        context: str,
        chunks: list[LLMContextChunk],
    ) -> LLMGenerationResult:
        """Generate an answer grounded in the supplied retrieval context."""
