"""
tests/test_retrieval_service.py
--------------------------------
Unit tests for the retrieval service.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.embeddings.embedding_service import PlaceholderEmbedder
from app.services.retrieval_service import (
    RetrievalErrorCode,
    RetrievalService,
)
from app.services.vector_store.qdrant_store import QdrantUnavailableError, VectorSearchResult


def _make_search_result(
    *,
    chunk_id: str,
    document_id: str,
    text: str,
    score: float,
    page_number: int = 1,
) -> VectorSearchResult:
    return VectorSearchResult(
        chunk_text=text,
        score=score,
        metadata={
            "chunk_id": chunk_id,
            "document_id": document_id,
            "page_number": page_number,
            "source_file": f"{document_id}.pdf",
        },
    )


@pytest.fixture
def vector_store() -> MagicMock:
    store = MagicMock()
    store.search.return_value = [
        _make_search_result(
            chunk_id="doc-1:chunk:0",
            document_id="doc-1",
            text="Revenue increased by 18% YoY.",
            score=0.91,
            page_number=3,
        ),
        _make_search_result(
            chunk_id="doc-1:chunk:1",
            document_id="doc-1",
            text="SaaS subscriptions drove growth.",
            score=0.84,
            page_number=4,
        ),
    ]
    return store


@pytest.fixture
def service(vector_store: MagicMock) -> RetrievalService:
    return RetrievalService(
        embedder=PlaceholderEmbedder(),
        vector_store=vector_store,
    )


@pytest.mark.asyncio
async def test_retrieves_relevant_chunks(service: RetrievalService, vector_store: MagicMock) -> None:
    result = await service.retrieve("What drove revenue growth?")

    assert result.status == "success"
    assert result.error is None
    assert result.query == "What drove revenue growth?"
    assert len(result.chunks) == 2
    assert result.chunks[0].chunk_id == "doc-1:chunk:0"
    assert result.chunks[0].document_id == "doc-1"
    assert result.chunks[0].page_number == 3
    assert result.chunks[0].text == "Revenue increased by 18% YoY."
    assert result.chunks[0].score == 0.91
    vector_store.search.assert_called_once()


@pytest.mark.asyncio
async def test_respects_top_k(vector_store: MagicMock) -> None:
    service = RetrievalService(embedder=PlaceholderEmbedder(), vector_store=vector_store)

    await service.retrieve("growth metrics", top_k=3)

    vector_store.search.assert_called_once()
    assert vector_store.search.call_args.kwargs["top_k"] == 3


@pytest.mark.asyncio
async def test_handles_empty_query(service: RetrievalService, vector_store: MagicMock) -> None:
    result = await service.retrieve("   ")

    assert result.status == "empty_query"
    assert result.chunks == []
    assert result.error is not None
    assert result.error.code is RetrievalErrorCode.EMPTY_QUERY
    vector_store.search.assert_not_called()


@pytest.mark.asyncio
async def test_handles_no_results(vector_store: MagicMock) -> None:
    vector_store.search.return_value = []
    service = RetrievalService(embedder=PlaceholderEmbedder(), vector_store=vector_store)

    result = await service.retrieve("unknown topic")

    assert result.status == "no_results"
    assert result.chunks == []
    assert result.error is not None
    assert result.error.code is RetrievalErrorCode.NO_RESULTS


@pytest.mark.asyncio
async def test_handles_qdrant_failure(vector_store: MagicMock) -> None:
    vector_store.search.side_effect = QdrantUnavailableError("Qdrant unreachable")
    service = RetrievalService(embedder=PlaceholderEmbedder(), vector_store=vector_store)

    result = await service.retrieve("revenue growth")

    assert result.status == "qdrant_unavailable"
    assert result.chunks == []
    assert result.error is not None
    assert result.error.code is RetrievalErrorCode.QDRANT_UNAVAILABLE
    assert "Qdrant unreachable" in (result.error.detail or "")


@pytest.mark.asyncio
async def test_handles_embedding_failure(vector_store: MagicMock) -> None:
    embedder = AsyncMock()
    embedder.embed.side_effect = RuntimeError("embedding backend unavailable")
    service = RetrievalService(embedder=embedder, vector_store=vector_store)

    result = await service.retrieve("revenue growth")

    assert result.status == "embedding_failed"
    assert result.chunks == []
    assert result.error is not None
    assert result.error.code is RetrievalErrorCode.EMBEDDING_FAILED
    vector_store.search.assert_not_called()
