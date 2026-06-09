from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.services.embeddings import EmbeddingService, BaseEmbedder
from app.services.vector_store.qdrant_store import (
    QdrantStore,
    QdrantStoreError,
    QdrantUnavailableError,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


class RetrievalErrorCode(str, Enum):
    EMPTY_QUERY = "EMPTY_QUERY"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    QDRANT_UNAVAILABLE = "QDRANT_UNAVAILABLE"
    NO_RESULTS = "NO_RESULTS"


@dataclass(frozen=True, slots=True)
class RetrievalError:
    code: RetrievalErrorCode
    message: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str
    score: float


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk]
    status: str = "success"
    error: RetrievalError | None = None
    search_time_ms: float = 0.0
    rerank_time_ms: float = 0.0


class RetrievalService:
    def __init__(
        self,
        *,
        embedder: BaseEmbedder | None = None,
        vector_store: QdrantStore | None = None,
    ) -> None:
        self._embedding_service = EmbeddingService(embedder=embedder)
        self._embedder = self._embedding_service._embedder
        self._vector_store = vector_store or QdrantStore(vector_dimension=self._embedder.dimension)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Any | None = None,
    ) -> RetrievalResult:
        logger.info(f"Retrieval requested: query='{query}', top_k={top_k}, filters={filters}")
        normalized_query = query.strip()
        if not normalized_query:
            logger.warning("Empty query submitted for retrieval.")
            return RetrievalResult(
                query=query,
                chunks=[],
                status="empty_query",
                error=RetrievalError(
                    code=RetrievalErrorCode.EMPTY_QUERY,
                    message="Query must not be empty.",
                ),
            )

        try:
            vectors = await self._embedder.embed([normalized_query])
        except Exception as exc:
            logger.error(f"Failed to generate query embedding: {exc}")
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="embedding_failed",
                error=RetrievalError(
                    code=RetrievalErrorCode.EMBEDDING_FAILED,
                    message="Failed to generate query embedding.",
                    detail=str(exc),
                ),
            )

        if not vectors or not vectors[0]:
            logger.error("Embedding service returned no vector for query.")
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="embedding_failed",
                error=RetrievalError(
                    code=RetrievalErrorCode.EMBEDDING_FAILED,
                    message="Embedding service returned no vector for query.",
                ),
            )

        search_time_ms = 0.0
        rerank_time_ms = 0.0  # Rerank is placeholder/0 for now
        
        try:
            start_search = time.perf_counter()
            search_results = self._vector_store.search(
                query_embedding=vectors[0],
                top_k=top_k,
                filters=filters,
            )
            search_time_ms = (time.perf_counter() - start_search) * 1000.0
            
            # Fallback to global search if no results and filters are active
            if not search_results and filters:
                has_filter = False
                if isinstance(filters, dict):
                    has_filter = any(v for v in filters.values() if v is not None)
                else:
                    has_filter = any([
                        getattr(filters, "document_ids", None),
                        getattr(filters, "tags", None),
                        getattr(filters, "filename", None),
                        getattr(filters, "upload_date", None),
                    ])
                if has_filter:
                    logger.info(f"Retrieval returned 0 chunks with active filters. Falling back to global search.")
                    start_search = time.perf_counter()
                    search_results = self._vector_store.search(
                        query_embedding=vectors[0],
                        top_k=top_k,
                        filters=None,
                    )
                    search_time_ms = (time.perf_counter() - start_search) * 1000.0
                    
        except QdrantUnavailableError as exc:
            logger.error(f"Qdrant unavailable during search: {exc}")
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="qdrant_unavailable",
                error=RetrievalError(
                    code=RetrievalErrorCode.QDRANT_UNAVAILABLE,
                    message="Qdrant vector search is unavailable.",
                    detail=str(exc),
                ),
            )
        except QdrantStoreError as exc:
            logger.error(f"Qdrant search store failed: {exc}")
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="qdrant_unavailable",
                error=RetrievalError(
                    code=RetrievalErrorCode.QDRANT_UNAVAILABLE,
                    message="Vector search failed.",
                    detail=str(exc),
                ),
            )

        if not search_results:
            logger.info(f"No results matched search query '{normalized_query}' after global fallback check.")
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="no_results",
                error=RetrievalError(
                    code=RetrievalErrorCode.NO_RESULTS,
                    message="No matching chunks found for query.",
                ),
                search_time_ms=search_time_ms,
                rerank_time_ms=rerank_time_ms,
            )

        logger.info(f"Retrieval query '{normalized_query}' matched {len(search_results)} chunk(s) in {search_time_ms:.2f}ms")
        return RetrievalResult(
            query=normalized_query,
            chunks=[_map_search_result(result) for result in search_results],
            status="success",
            search_time_ms=search_time_ms,
            rerank_time_ms=rerank_time_ms,
        )


def _map_search_result(result: VectorSearchResult) -> RetrievedChunk:
    metadata = result.metadata
    chunk_id = metadata.get("chunk_id") or ""
    document_id = metadata.get("document_id") or ""
    page_number = metadata.get("page_number")
    if not isinstance(page_number, int):
        page_number = 0

    return RetrievedChunk(
        chunk_id=str(chunk_id),
        document_id=str(document_id),
        page_number=page_number,
        text=result.chunk_text,
        score=result.score,
    )
