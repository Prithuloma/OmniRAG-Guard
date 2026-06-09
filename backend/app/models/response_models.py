"""
Response schemas for OmniRAG-Guard API.

Design rules:
  - All responses wrap data in a shared BaseResponse envelope.
  - Error responses are consistent and machine-readable.
  - RAG-specific fields (confidence, latency_ms, chunks) live here only.
"""
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.models.base import DocumentStatus, QueryStatus


# ── Envelope ─────────────────────────────────────────────────────────────────

class BaseResponse(BaseModel):
    """
    Universal response wrapper.
    Every endpoint returns a subclass of this; frontends can always
    rely on `success`, `message`, and `timestamp` being present.
    """
    success: bool = Field(description="Whether the request was fulfilled.")
    message: str = Field(description="Human-readable result summary.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC time the response was generated (ISO-8601).",
    )


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Machine-readable detail block inside an error response."""
    code: str = Field(
        description="Snake-case error token for programmatic handling.",
        examples=["invalid_file_type", "query_timeout"],
    )
    field: Optional[str] = Field(
        default=None,
        description="Request field that triggered the error, if applicable.",
        examples=["query"],
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional structured context for debugging.",
    )


class ErrorResponse(BaseResponse):
    """Returned on any 4xx / 5xx."""
    success: bool = False
    error: ErrorDetail = Field(description="Structured error detail.")


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseResponse):
    """Returned by POST /upload on acceptance."""
    success: bool = True
    document_id: str = Field(
        default_factory=lambda: f"doc_{uuid4().hex[:12]}",
        description="Stable identifier assigned to the ingested document.",
        examples=["doc_a1b2c3d4e5f6"],
    )
    filename: str = Field(
        description="Original filename as received.",
        examples=["q3-report.pdf"],
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        description="Initial pipeline state; poll or subscribe for updates.",
    )


class UploadIngestionResponse(BaseModel):
    """Returned by POST /upload after validation, storage, and ingestion."""
    document_id: str = Field(
        description="Stable identifier assigned to the ingested document.",
        examples=["doc_a1b2c3d4e5f6"],
    )
    status: str = Field(
        description="Ingestion pipeline outcome.",
        examples=["success"],
    )
    chunks_created: int = Field(
        ge=0,
        description="Number of text chunks generated from the document.",
        examples=[12],
    )
    vectors_stored: int = Field(
        ge=0,
        description="Number of vectors upserted into the vector store.",
        examples=[12],
    )


# ── Query ─────────────────────────────────────────────────────────────────────

class RetrievedChunk(BaseModel):
    """
    A single context chunk surfaced by the retrieval step.
    Kept flat so frontends can render chunk cards without transformation.
    """
    chunk_id: str = Field(
        description="Stable identifier for this chunk.",
        examples=["chunk_001"],
    )
    document_id: str = Field(
        description="Parent document this chunk belongs to.",
        examples=["doc_a1b2c3d4e5f6"],
    )
    page_number: int = Field(
        default=0,
        ge=0,
        description="Source page in the original document, if available.",
        examples=[4],
    )
    text: str = Field(
        description="Raw chunk text passed to the LLM as context.",
        examples=["Revenue increased by 18% YoY driven by SaaS subscriptions."],
    )
    score: float = Field(
        description="Similarity score returned by the vector store for this chunk.",
        examples=[0.87],
    )


class Citation(BaseModel):
    """Source attribution for LLM generated answers."""
    document_id: str = Field(description="Parent document identifier.")
    chunk_id: str = Field(description="Source chunk identifier.")
    page_number: int = Field(default=0, description="Source page number if available.")


class RetrievalStats(BaseModel):
    """Detailed performance metrics for the retrieval step."""
    chunks_retrieved: int = Field(description="Number of chunks retrieved.")
    search_time_ms: float = Field(description="Time spent searching in the vector database.")
    rerank_time_ms: float = Field(default=0.0, description="Time spent reranking retrieved chunks.")


class QueryResponse(BaseResponse):
    """Returned by POST /query on completion."""
    success: bool = True
    query_id: str = Field(
        default_factory=lambda: f"qry_{uuid4().hex[:12]}",
        description="Unique identifier for this query execution.",
        examples=["qry_f7e8d9c0b1a2"],
    )
    query: str = Field(
        description="Normalized query string executed against the retrieval pipeline.",
        examples=["What were the key revenue drivers in Q3 2024?"],
    )
    status: QueryStatus = Field(
        description="Resolution quality of the query.",
    )
    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Ordered list of context chunks retrieved for the query.",
    )
    chunk_count: int = Field(
        ge=0,
        description="Number of chunks returned in retrieved_chunks.",
        examples=[3],
    )
    latency_ms: float = Field(
        ge=0.0,
        description="Total wall-clock time for retrieval in milliseconds.",
        examples=[420.5],
    )
    answer: str = Field(
        default="",
        description="LLM-generated answer grounded in retrieved chunks.",
        examples=["Q3 2024 revenue grew 18% YoY, primarily driven by SaaS."],
    )
    confidence: float = Field(
        default=0.0,
        description="Blended confidence score from retrieval and evidence verification.",
        examples=[0.85],
    )
    evidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Lexical evidence score measuring answer support in retrieved chunks.",
        examples=[0.82],
    )
    grounding_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Blended lexical and semantic grounding score.",
        examples=[0.81],
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="List of source citations attributing the generated answer.",
    )
    retrieval_stats: Optional[RetrievalStats] = Field(
        default=None,
        description="Detailed performance metrics for retrieval.",
    )
    grounded: bool = Field(
        default=False,
        description="Whether the generated answer is supported by retrieved evidence.",
    )
    verification_reason: str = Field(
        default="",
        description="Human-readable explanation of the verification outcome.",
        examples=["Answer is supported by retrieved chunks."],
    )

    @model_validator(mode="after")
    def _clamp_confidence_on_failed(self) -> "QueryResponse":
        """Confidence must be 0 when status is FAILED — enforced at model level."""
        if self.status in {QueryStatus.FAILED, QueryStatus.NO_RESULTS}:
            self.confidence = 0.0
            self.evidence_score = 0.0
            self.grounding_score = 0.0
            self.grounded = False
            self.citations = []
        return self
