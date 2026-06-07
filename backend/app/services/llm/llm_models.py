from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMContextChunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMGenerationResult:
    answer: str
    confidence: float
    success: bool = True
    provider: str = "mock"
    metadata: dict[str, Any] = field(default_factory=dict)
