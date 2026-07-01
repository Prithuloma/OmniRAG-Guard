"""
tests/test_embeddings.py
------------------------
Unit tests for embedding layer foundation.
"""

from __future__ import annotations

import pytest

from app.services.chunking.chunk_models import Chunk
from app.services.embeddings.embedding_service import (
    DEFAULT_EMBEDDING_DIMENSION,
    EmbeddingService,
    PlaceholderEmbedder,
    deterministic_vector,
)


def _make_chunk(*, chunk_id: str, content: str, chunk_index: int) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        content=content,
        chunk_index=chunk_index,
        start_char=chunk_index * 100,
        end_char=chunk_index * 100 + len(content),
        metadata={"chunk_index": chunk_index},
    )


@pytest.mark.asyncio
async def test_embedding_generation() -> None:
    service = EmbeddingService()
    chunks = [_make_chunk(chunk_id="doc-1:chunk:0", content="hello world", chunk_index=0)]

    result = await service.embed_chunks(chunks)

    assert result.success is True
    assert result.total_embeddings == 1
    assert len(result.embeddings) == 1


@pytest.mark.asyncio
async def test_embedding_dimensions() -> None:
    service = EmbeddingService()
    chunks = [_make_chunk(chunk_id="doc-1:chunk:0", content="dimension check", chunk_index=0)]

    result = await service.embed_chunks(chunks)
    embedding = result.embeddings[0]

    assert embedding.dimension == DEFAULT_EMBEDDING_DIMENSION
    assert len(embedding.vector) == DEFAULT_EMBEDDING_DIMENSION


@pytest.mark.asyncio
async def test_chunk_to_embedding_mapping() -> None:
    service = EmbeddingService()
    chunks = [
        _make_chunk(chunk_id="doc-1:chunk:0", content="first chunk", chunk_index=0),
        _make_chunk(chunk_id="doc-1:chunk:1", content="second chunk", chunk_index=1),
    ]

    result = await service.embed_chunks(chunks)

    assert result.total_embeddings == 2
    assert result.embeddings[0].chunk_id == "doc-1:chunk:0"
    assert result.embeddings[0].embedding_id == "doc-1:chunk:0:embedding"
    assert result.embeddings[1].chunk_id == "doc-1:chunk:1"
    assert result.embeddings[1].metadata["chunk_index"] == 1


def test_deterministic_outputs() -> None:
    text = "deterministic embedding input"
    first = deterministic_vector(text)
    second = deterministic_vector(text)

    assert first == second


@pytest.mark.asyncio
async def test_multiple_chunks() -> None:
    embedder = PlaceholderEmbedder()
    service = EmbeddingService(embedder=embedder)
    chunks = [
        _make_chunk(chunk_id=f"doc-1:chunk:{index}", content=f"chunk {index}", chunk_index=index)
        for index in range(5)
    ]

    result = await service.embed_chunks(chunks)

    assert result.success is True
    assert result.total_embeddings == 5
    assert [embedding.chunk_id for embedding in result.embeddings] == [
        chunk.chunk_id for chunk in chunks
    ]
    assert all(embedding.dimension == embedder.dimension for embedding in result.embeddings)


@pytest.mark.asyncio
async def test_empty_chunks_returns_empty_result() -> None:
    service = EmbeddingService()

    result = await service.embed_chunks([])

    assert result.success is True
    assert result.total_embeddings == 0
    assert result.embeddings == []
