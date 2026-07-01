from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.models.request_models import QueryFilters
from app.services.retrieval_service import RetrievedChunk
from app.services.verification.verification_models import VerificationResult


@dataclass
class WorkflowState:
    """
    WorkflowState coordinates pipeline parameters, intermediate status,
    and results through the retrieval-generation-verification workflow.
    """
    query: str
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    generated_answer: str = ""
    verification_result: Optional[VerificationResult] = None
    final_confidence: float = 0.0
    filters: Optional[QueryFilters] = None
    execution_metadata: dict[str, Any] = field(default_factory=dict)
