from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class VerificationResult:
    evidence_score: float
    grounded: bool
    verification_reason: str
    confidence: float
    retrieval_confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
