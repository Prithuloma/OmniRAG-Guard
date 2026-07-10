from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChunkingResult:
    success: bool
    total_chunks: int
    chunks: list[Chunk]
