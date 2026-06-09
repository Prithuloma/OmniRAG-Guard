"""
Request schemas for OmniRAG-Guard API.

Design rules:
  - Every field carries a description for OpenAPI auto-docs.
  - Optional fields have sensible defaults so frontends can omit them.
  - No business logic; pure data contracts.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadMetadata(BaseModel):
    """
    Optional caller-supplied metadata attached to an uploaded document.
    Stored as-is and forwarded to the ingestion pipeline.
    """
    title: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Human-readable document title.",
        examples=["Q3 Financial Report 2024"],
    )
    source: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Origin URL or path of the document.",
        examples=["https://example.com/docs/q3-report.pdf"],
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Arbitrary labels for downstream filtering.",
        examples=[["finance", "quarterly"]],
    )


class UploadRequest(BaseModel):
    """
    Body for POST /upload.
    The file itself arrives as multipart/form-data; this model covers
    the JSON metadata part of the same request.
    """
    metadata: UploadMetadata = Field(
        default_factory=UploadMetadata,
        description="Optional document metadata.",
    )


# ── Query ─────────────────────────────────────────────────────────────────────

class QueryFilters(BaseModel):
    """
    Optional scoping applied before retrieval.
    All fields are nullable so the RAG pipeline can skip filtering cleanly.
    """
    document_ids: Optional[list[str]] = Field(
        default=None,
        description="Restrict retrieval to these document IDs.",
        examples=[["doc_abc123", "doc_def456"]],
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Restrict retrieval to this single document ID.",
        examples=["doc_abc123"],
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Restrict retrieval to documents carrying all these tags.",
        examples=[["finance"]],
    )
    filename: Optional[str] = Field(
        default=None,
        description="Restrict retrieval to this source filename.",
        examples=["annual_report.pdf"],
    )
    upload_date: Optional[str] = Field(
        default=None,
        description="Restrict retrieval to this upload date.",
        examples=["2026-06-09"],
    )


class QueryRequest(BaseModel):
    """Body for POST /query."""
    query: str = Field(
        min_length=1,
        max_length=2048,
        description="Natural-language question sent to the RAG pipeline.",
        examples=["What were the key revenue drivers in Q3 2024?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of chunks to retrieve.",
    )
    filters: QueryFilters = Field(
        default_factory=QueryFilters,
        description="Optional retrieval scope.",
    )
