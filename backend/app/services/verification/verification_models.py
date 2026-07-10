from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class VerificationResult:
    evidence_score: float
    grounded: bool
    verification_reason: str
    confidence: float
    grounding_score: float = 0.0
    citations: list[dict[str, Any]] = field(default_factory=list)
    retrieval_confidence: float = 0.0
    claims: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
