from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Embedding:
    embedding_id: str
    chunk_id: str
    vector: list[float]
    dimension: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    success: bool
    total_embeddings: int
    embeddings: list[Embedding]
