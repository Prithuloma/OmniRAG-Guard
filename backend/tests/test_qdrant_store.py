"""
tests/test_qdrant_store.py
--------------------------
Integration tests for Qdrant vector store operations.
"""

from __future__ import annotations

import uuid

import pytest

from app.services.chunking.chunk_models import Chunk
from app.services.embeddings.embedding_models import Embedding
from app.services.embeddings.embedding_service import (
    DEFAULT_EMBEDDING_DIMENSION,
    deterministic_vector,
)
from app.services.vector_store.qdrant_store import (
    CollectionMissingError,
    EmptyVectorsError,
    MalformedPayloadError,
    QdrantStore,
    QdrantUnavailableError,
)

QDRANT_URL = "http://localhost:6333"


def _qdrant_skip_reason(url: str = QDRANT_URL) -> str | None:
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        return "qdrant-client package is not installed"

    try:
        client = QdrantClient(url=url, timeout=5.0)
        client.get_collections()
    except Exception as exc:
        return f"Qdrant is not reachable at {url}: {exc}"

    return None


@pytest.fixture(scope="session")
def qdrant_url() -> str:
    return QDRANT_URL


@pytest.fixture
def require_qdrant(qdrant_url: str) -> str:
    skip_reason = _qdrant_skip_reason(qdrant_url)
    if skip_reason is not None:
        pytest.skip(skip_reason)
    return qdrant_url


@pytest.fixture
def collection_name() -> str:
    return f"omnirag_test_{uuid.uuid4().hex}"


@pytest.fixture
def store(require_qdrant: str, collection_name: str) -> QdrantStore:
    from qdrant_client import QdrantClient

    qdrant_store = QdrantStore(
        url=require_qdrant,
        collection_name=collection_name,
        vector_dimension=DEFAULT_EMBEDDING_DIMENSION,
    )
    yield qdrant_store
    client = QdrantClient(url=require_qdrant, timeout=5.0)
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)


def _make_chunk(
    *,
    chunk_id: str,
    document_id: str,
    content: str,
    chunk_index: int,
    page_number: int | None = None,
) -> Chunk:
    metadata: dict[str, object] = {
        "file_name": f"{document_id}.pdf",
        "chunk_index": chunk_index,
    }
    if page_number is not None:
        metadata["page_number"] = page_number

    return Chunk(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        chunk_index=chunk_index,
        start_char=chunk_index * 100,
        end_char=chunk_index * 100 + len(content),
        metadata=metadata,
    )


def _make_embedding(*, chunk: Chunk) -> Embedding:
    return Embedding(
        embedding_id=f"{chunk.chunk_id}:embedding",
        chunk_id=chunk.chunk_id,
        vector=deterministic_vector(chunk.content),
        dimension=DEFAULT_EMBEDDING_DIMENSION,
        metadata={"document_id": chunk.document_id},
    )


def test_initialize_collection_creates_collection(store: QdrantStore, require_qdrant: str) -> None:
    from qdrant_client import QdrantClient

    store.initialize_collection()

    client = QdrantClient(url=require_qdrant, timeout=5.0)
    assert client.collection_exists(store.collection_name)

    info = client.get_collection(store.collection_name)
    assert info.config.params.vectors.size == DEFAULT_EMBEDDING_DIMENSION
    assert info.config.params.vectors.distance.name == "COSINE"


def test_upsert_chunks_inserts_vectors(store: QdrantStore) -> None:
    chunk = _make_chunk(
        chunk_id="doc-1:chunk:0",
        document_id="doc-1",
        content="vector store insert test",
        chunk_index=0,
        page_number=1,
    )
    embedding = _make_embedding(chunk=chunk)

    inserted = store.upsert_chunks(chunks=[chunk], embeddings=[embedding])

    assert inserted == 1


def test_search_returns_matching_vectors(store: QdrantStore) -> None:
    chunk = _make_chunk(
        chunk_id="doc-2:chunk:0",
        document_id="doc-2",
        content="searchable chunk content",
        chunk_index=0,
        page_number=2,
    )
    embedding = _make_embedding(chunk=chunk)
    store.upsert_chunks(chunks=[chunk], embeddings=[embedding])

    results = store.search(
        query_embedding=deterministic_vector("searchable chunk content"),
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].chunk_text == chunk.content
    assert isinstance(results[0].score, float)


def test_delete_document_removes_vectors(store: QdrantStore) -> None:
    chunks = [
        _make_chunk(
            chunk_id=f"doc-3:chunk:{index}",
            document_id="doc-3",
            content=f"chunk {index}",
            chunk_index=index,
        )
        for index in range(3)
    ]
    embeddings = [_make_embedding(chunk=chunk) for chunk in chunks]
    store.upsert_chunks(chunks=chunks, embeddings=embeddings)

    deleted = store.delete_document(document_id="doc-3")

    assert deleted == 3
    results = store.search(
        query_embedding=deterministic_vector("chunk 0"),
        top_k=3,
    )
    assert all(result.metadata.get("document_id") != "doc-3" for result in results)


def test_metadata_preservation(store: QdrantStore) -> None:
    chunk = _make_chunk(
        chunk_id="doc-4:chunk:0",
        document_id="doc-4",
        content="metadata preservation test",
        chunk_index=0,
        page_number=7,
    )
    embedding = _make_embedding(chunk=chunk)
    store.upsert_chunks(chunks=[chunk], embeddings=[embedding])

    results = store.search(
        query_embedding=deterministic_vector(chunk.content),
        top_k=1,
    )

    metadata = results[0].metadata
    assert metadata["document_id"] == "doc-4"
    assert metadata["chunk_id"] == "doc-4:chunk:0"
    assert metadata["page_number"] == 7
    assert metadata["source_file"] == "doc-4.pdf"
    assert results[0].chunk_text == "metadata preservation test"


def test_upsert_rejects_empty_vectors() -> None:
    store = QdrantStore(
        url=QDRANT_URL,
        collection_name="omnirag_validation_test",
        vector_dimension=DEFAULT_EMBEDDING_DIMENSION,
    )

    with pytest.raises(EmptyVectorsError):
        store.upsert_chunks(chunks=[], embeddings=[])


def test_upsert_rejects_mismatched_pairs() -> None:
    store = QdrantStore(
        url=QDRANT_URL,
        collection_name="omnirag_validation_test",
        vector_dimension=DEFAULT_EMBEDDING_DIMENSION,
    )
    chunk = _make_chunk(
        chunk_id="doc-5:chunk:0",
        document_id="doc-5",
        content="mismatch test",
        chunk_index=0,
    )
    embedding = _make_embedding(chunk=chunk)
    embedding = Embedding(
        embedding_id=embedding.embedding_id,
        chunk_id="different-chunk",
        vector=embedding.vector,
        dimension=embedding.dimension,
        metadata=embedding.metadata,
    )

    with pytest.raises(MalformedPayloadError):
        store.upsert_chunks(chunks=[chunk], embeddings=[embedding])


def test_search_requires_existing_collection(require_qdrant: str) -> None:
    store = QdrantStore(
        url=require_qdrant,
        collection_name=f"omnirag_missing_{uuid.uuid4().hex}",
        vector_dimension=DEFAULT_EMBEDDING_DIMENSION,
    )

    with pytest.raises(CollectionMissingError):
        store.search(
            query_embedding=deterministic_vector("missing collection"),
            top_k=1,
        )


def test_unavailable_qdrant_raises() -> None:
    from unittest.mock import patch
    store = QdrantStore(
        url="http://localhost:6399",
        collection_name="omnirag_unreachable",
        vector_dimension=DEFAULT_EMBEDDING_DIMENSION,
    )

    with patch("app.services.vector_store.qdrant_store.QdrantClient", side_effect=Exception("Qdrant unavailable")):
        with pytest.raises(QdrantUnavailableError):
            store.initialize_collection()

