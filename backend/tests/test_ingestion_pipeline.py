"""
tests/test_ingestion_pipeline.py
--------------------------------
Unit tests for the end-to-end document ingestion pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import fitz
import pytest

from app.services.chunking.text_chunker import TextChunker
from app.services.embeddings.embedding_models import EmbeddingResult
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.ingestion.ingestion_pipeline import (
    DocumentIngestionPipeline,
    IngestionErrorCode,
    ingest_document,
)
from app.services.ingestion.parser_dispatcher import ParserDispatchStatus, ParserDispatcher
from app.services.ingestion.parsers.base_parser import ParseResult, ParseStatus, ParserType
from app.services.vector_store.qdrant_store import QdrantUnavailableError


def _make_pdf_with_text(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def _make_empty_pdf() -> bytes:
    document = fitz.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def _write_pdf(path: Path, *, text: str | None = None) -> None:
    data = _make_empty_pdf() if text is None else _make_pdf_with_text(text)
    path.write_bytes(data)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.pdf"
    _write_pdf(file_path, text="OmniRAG ingestion pipeline end-to-end test content.")
    return file_path


@pytest.fixture
def empty_pdf(tmp_path: Path) -> Path:
    file_path = tmp_path / "empty.pdf"
    _write_pdf(file_path)
    return file_path


@pytest.fixture
def pipeline_with_mock_store() -> tuple[DocumentIngestionPipeline, MagicMock]:
    vector_store = MagicMock()
    vector_store.upsert_chunks.return_value = 1

    pipeline = DocumentIngestionPipeline(
        parser_dispatcher=ParserDispatcher(),
        chunker=TextChunker(),
        embedder=EmbeddingService(),
        vector_store=vector_store,
    )
    return pipeline, vector_store


@pytest.mark.asyncio
async def test_successful_end_to_end_ingestion(
    sample_pdf: Path,
    pipeline_with_mock_store: tuple[DocumentIngestionPipeline, MagicMock],
) -> None:
    pipeline, vector_store = pipeline_with_mock_store

    result = await pipeline.ingest(
        document_id="doc-e2e-1",
        file_path=str(sample_pdf),
        metadata={"tenant_id": "tenant-a", "content_type": "application/pdf"},
    )

    assert result.document_id == "doc-e2e-1"
    assert result.status == "success"
    assert result.error is None
    assert result.pages_processed == 1
    assert result.chunks_created == 1
    assert result.vectors_stored == 1
    assert result.processing_time_ms >= 0.0

    vector_store.upsert_chunks.assert_called_once()
    upsert_kwargs = vector_store.upsert_chunks.call_args.kwargs
    assert len(upsert_kwargs["chunks"]) == 1
    assert len(upsert_kwargs["embeddings"]) == 1


@pytest.mark.asyncio
async def test_empty_document_handling(
    empty_pdf: Path,
    pipeline_with_mock_store: tuple[DocumentIngestionPipeline, MagicMock],
) -> None:
    pipeline, vector_store = pipeline_with_mock_store

    result = await pipeline.ingest(
        document_id="doc-empty-1",
        file_path=str(empty_pdf),
        metadata={"content_type": "application/pdf"},
    )

    assert result.status == "empty"
    assert result.pages_processed == 1
    assert result.chunks_created == 0
    assert result.vectors_stored == 0
    assert result.error is not None
    assert result.error.code is IngestionErrorCode.EMPTY_DOCUMENT
    vector_store.upsert_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_parser_failure_handling(tmp_path: Path) -> None:
    file_path = tmp_path / "broken.pdf"
    file_path.write_bytes(b"%PDF-not-valid")

    failing_parser = AsyncMock()
    failing_parser.parse.return_value = ParseResult(
        parser_type=ParserType.PDF,
        file_name="broken.pdf",
        status=ParseStatus.FAILED,
        extracted_text="",
        metadata={"page_count": 0},
    )

    dispatcher = AsyncMock()
    dispatch_result = MagicMock()
    dispatch_result.status = ParserDispatchStatus.SELECTED
    dispatch_result.parser = failing_parser
    dispatch_result.parser_type = ParserType.PDF
    dispatch_result.file_extension = ".pdf"
    dispatcher.dispatch = AsyncMock(return_value=dispatch_result)

    pipeline = DocumentIngestionPipeline(
        parser_dispatcher=dispatcher,
        chunker=TextChunker(),
        embedder=EmbeddingService(),
        vector_store=MagicMock(),
    )

    result = await pipeline.ingest(
        document_id="doc-parser-fail",
        file_path=str(file_path),
        metadata={"content_type": "application/pdf"},
    )

    assert result.status == "parser_failed"
    assert result.error is not None
    assert result.error.code is IngestionErrorCode.PARSER_FAILED
    assert result.chunks_created == 0
    assert result.vectors_stored == 0


@pytest.mark.asyncio
async def test_embedding_failure_handling(sample_pdf: Path) -> None:
    embedder = AsyncMock()
    embedder.embed_chunks.side_effect = RuntimeError("embedding backend unavailable")

    pipeline = DocumentIngestionPipeline(
        parser_dispatcher=ParserDispatcher(),
        chunker=TextChunker(),
        embedder=embedder,
        vector_store=MagicMock(),
    )

    result = await pipeline.ingest(
        document_id="doc-embed-fail",
        file_path=str(sample_pdf),
        metadata={"content_type": "application/pdf"},
    )

    assert result.status == "embedding_failed"
    assert result.error is not None
    assert result.error.code is IngestionErrorCode.EMBEDDING_FAILED
    assert result.chunks_created == 1
    assert result.vectors_stored == 0
    assert "embedding backend unavailable" in (result.error.detail or "")


@pytest.mark.asyncio
async def test_vector_store_failure_handling(sample_pdf: Path) -> None:
    vector_store = MagicMock()
    vector_store.upsert_chunks.side_effect = QdrantUnavailableError("Qdrant unreachable")

    pipeline = DocumentIngestionPipeline(
        parser_dispatcher=ParserDispatcher(),
        chunker=TextChunker(),
        embedder=EmbeddingService(),
        vector_store=vector_store,
    )

    result = await pipeline.ingest(
        document_id="doc-store-fail",
        file_path=str(sample_pdf),
        metadata={"content_type": "application/pdf"},
    )

    assert result.status == "vector_store_failed"
    assert result.error is not None
    assert result.error.code is IngestionErrorCode.VECTOR_STORE_FAILED
    assert result.chunks_created == 1
    assert result.vectors_stored == 0
    assert "Qdrant unreachable" in (result.error.detail or "")


@pytest.mark.asyncio
async def test_metadata_propagation(
    sample_pdf: Path,
    pipeline_with_mock_store: tuple[DocumentIngestionPipeline, MagicMock],
) -> None:
    pipeline, vector_store = pipeline_with_mock_store
    metadata: dict[str, Any] = {
        "tenant_id": "tenant-b",
        "source": "upload",
        "content_type": "application/pdf",
    }

    result = await ingest_document(
        document_id="doc-meta-1",
        file_path=str(sample_pdf),
        metadata=metadata,
        pipeline=pipeline,
    )

    assert result.status == "success"

    chunk = vector_store.upsert_chunks.call_args.kwargs["chunks"][0]
    assert chunk.document_id == "doc-meta-1"
    assert chunk.metadata["tenant_id"] == "tenant-b"
    assert chunk.metadata["source"] == "upload"
    assert chunk.metadata["file_name"] == "sample.pdf"
    assert chunk.metadata["parser_type"] == ParserType.PDF.value


@pytest.mark.asyncio
async def test_embedding_empty_result_is_treated_as_failure(sample_pdf: Path) -> None:
    embedder = AsyncMock()
    embedder.embed_chunks.return_value = EmbeddingResult(
        success=False,
        total_embeddings=0,
        embeddings=[],
    )

    pipeline = DocumentIngestionPipeline(
        parser_dispatcher=ParserDispatcher(),
        chunker=TextChunker(),
        embedder=embedder,
        vector_store=MagicMock(),
    )

    result = await pipeline.ingest(
        document_id="doc-embed-empty",
        file_path=str(sample_pdf),
        metadata={"content_type": "application/pdf"},
    )

    assert result.status == "embedding_failed"
    assert result.error is not None
    assert result.error.code is IngestionErrorCode.EMBEDDING_FAILED
