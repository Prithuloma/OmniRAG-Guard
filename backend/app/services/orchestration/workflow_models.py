from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.models.response_models import RetrievedChunk as ApiRetrievedChunk


class WorkflowStatus(str, Enum):
    """Execution status of the RAG pipeline workflow."""
    PENDING = "pending"
    RETRIEVING = "retrieving"
    GENERATING = "generating"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryPipelineErrorCode(str, Enum):
    EMPTY_QUERY = "EMPTY_QUERY"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    QDRANT_UNAVAILABLE = "QDRANT_UNAVAILABLE"
    NO_RESULTS = "NO_RESULTS"
    GENERATION_FAILED = "GENERATION_FAILED"


@dataclass(frozen=True, slots=True)
class QueryPipelineError:
    code: QueryPipelineErrorCode
    message: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class QueryPipelineResult:
    query_id: str
    query: str
    status: str
    retrieved_chunks: list[ApiRetrievedChunk]
    chunk_count: int
    latency_ms: float
    answer: str = ""
    confidence: float = 0.0
    evidence_score: float = 0.0
    grounding_score: float = 0.0
    citations: list[dict[str, Any]] = field(default_factory=list)
    retrieval_stats: dict[str, Any] | None = None
    grounded: bool = False
    verification_reason: str = ""
    conversation_title: str = ""
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    verification_time_ms: float = 0.0
    embedding_model: str = ""
    llm_model: str = ""
    semantic_similarity: float = 0.0
    lexical_overlap: float = 0.0
    consensus_score: float = field(default=0.0)
    claims: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    error: QueryPipelineError | None = None
