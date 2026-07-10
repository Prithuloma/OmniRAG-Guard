"""
Shared base types used by both request and response schemas.
Import from here to keep request_models / response_models thin.
"""
from enum import Enum


class DocumentStatus(str, Enum):
    """Lifecycle state of an ingested document."""
    PENDING    = "pending"
    PROCESSING = "processing"
    READY      = "ready"
    FAILED     = "failed"


class QueryStatus(str, Enum):
    """Resolution state of a RAG query."""
    SUCCESS = "success"
    PARTIAL = "partial"   # answer found but low-confidence chunks
    NO_RESULTS = "no_results"
    FAILED  = "failed"
