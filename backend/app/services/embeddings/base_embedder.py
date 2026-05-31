from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimension produced by this embedder."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return one vector per text."""
