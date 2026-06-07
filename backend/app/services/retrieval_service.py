from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.embeddings.base_embedder import BaseEmbedder
from app.services.embeddings.embedding_service import PlaceholderEmbedder
from app.services.vector_store.qdrant_store import (
    QdrantStore,
    QdrantStoreError,
    QdrantUnavailableError,
    VectorSearchResult,
)


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


class RetrievalService:
    def __init__(
        self,
        *,
        embedder: BaseEmbedder | None = None,
        vector_store: QdrantStore | None = None,
    ) -> None:
        self._embedder = embedder or PlaceholderEmbedder()
        self._vector_store = vector_store or QdrantStore()

    async def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        normalized_query = query.strip()
        if not normalized_query:
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
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="embedding_failed",
                error=RetrievalError(
                    code=RetrievalErrorCode.EMBEDDING_FAILED,
                    message="Embedding service returned no vector for query.",
                ),
            )

        try:
            search_results = self._vector_store.search(
                query_embedding=vectors[0],
                top_k=top_k,
            )
        except QdrantUnavailableError as exc:
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
            return RetrievalResult(
                query=normalized_query,
                chunks=[],
                status="no_results",
                error=RetrievalError(
                    code=RetrievalErrorCode.NO_RESULTS,
                    message="No matching chunks found for query.",
                ),
            )

        return RetrievalResult(
            query=normalized_query,
            chunks=[_map_search_result(result) for result in search_results],
            status="success",
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
