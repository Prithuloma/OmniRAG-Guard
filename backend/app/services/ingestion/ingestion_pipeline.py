"""
ingestion_pipeline.py
---------------------
End-to-end document ingestion pipeline.

Upload validation entry point (``run_ingestion_pipeline``) remains unchanged for
API compatibility. Full parse → chunk → embed → Qdrant flow lives in
``DocumentIngestionPipeline`` / ``ingest_document``.
"""

from __future__ import annotations

import logging
import mimetypes
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

from fastapi import UploadFile

from app.services.chunking.text_chunker import TextChunker
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.ingestion.file_validator import validate_upload_file
from app.services.ingestion.parser_dispatcher import (
    ParserDispatcher,
    ParserDispatchStatus,
)
from app.services.ingestion.parsers.base_parser import ParseResult, ParseStatus
from app.services.ingestion.validation import FileValidationResult
from app.services.vector_store.qdrant_store import QdrantStore, QdrantStoreError

if TYPE_CHECKING:
    from app.services.ingestion_service import UploadIngestionResult

logger = logging.getLogger(__name__)


class IngestionErrorCode(str, Enum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    PARSER_FAILED = "PARSER_FAILED"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    VECTOR_STORE_FAILED = "VECTOR_STORE_FAILED"


@dataclass(frozen=True, slots=True)
class IngestionError:
    code: IngestionErrorCode
    message: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document_id: str
    status: str
    pages_processed: int = 0
    chunks_created: int = 0
    vectors_stored: int = 0
    processing_time_ms: float = 0.0
    error: IngestionError | None = None


class DocumentIngestionPipeline:
    def __init__(
        self,
        *,
        parser_dispatcher: ParserDispatcher | None = None,
        chunker: TextChunker | None = None,
        embedder: EmbeddingService | None = None,
        vector_store: QdrantStore | None = None,
    ) -> None:
        self._parser_dispatcher = parser_dispatcher or ParserDispatcher()
        self._chunker = chunker or TextChunker()
        self._embedder = embedder or EmbeddingService()
        self._vector_store = vector_store or QdrantStore(vector_dimension=self._embedder.dimension)

    async def ingest(
        self,
        *,
        document_id: str,
        file_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        started_at = time.perf_counter()
        input_metadata: dict[str, Any] = dict(metadata or {})

        path = Path(file_path)
        if not path.is_file():
            return self._error_result(
                document_id=document_id,
                status="file_not_found",
                started_at=started_at,
                error=IngestionError(
                    code=IngestionErrorCode.FILE_NOT_FOUND,
                    message=f"File not found: {file_path}",
                ),
            )

        filename = path.name
        data = path.read_bytes()
        content_type = input_metadata.get("content_type") or mimetypes.guess_type(filename)[0]
        if not content_type:
            content_type = "application/octet-stream"

        dispatch_result = await self._parser_dispatcher.dispatch(
            filename=filename,
            content_type=content_type,
            data=data,
        )

        if (
            dispatch_result.status is not ParserDispatchStatus.SELECTED
            or dispatch_result.parser is None
        ):
            return self._error_result(
                document_id=document_id,
                status="unsupported_file_type",
                started_at=started_at,
                error=IngestionError(
                    code=IngestionErrorCode.UNSUPPORTED_FILE_TYPE,
                    message=f"Unsupported file type for '{filename}'.",
                    detail=f"extension={dispatch_result.file_extension}",
                ),
            )

        logger.info(
            "Parsing started: document_id=%s file_path=%s parser=%s",
            document_id,
            file_path,
            dispatch_result.parser_type,
        )

        parse_result = await dispatch_result.parser.parse(
            filename=filename,
            content_type=content_type,
            data=data,
        )

        pages_processed = _pages_processed(parse_result)

        logger.info(
            "Parsing completed: document_id=%s status=%s pages_processed=%d",
            document_id,
            parse_result.status.value,
            pages_processed,
        )

        if parse_result.status is ParseStatus.FAILED:
            return self._error_result(
                document_id=document_id,
                status="parser_failed",
                started_at=started_at,
                pages_processed=pages_processed,
                error=IngestionError(
                    code=IngestionErrorCode.PARSER_FAILED,
                    message=f"Failed to parse '{filename}'.",
                    detail=f"parser_type={parse_result.parser_type.value}",
                ),
            )

        if parse_result.status is ParseStatus.EMPTY or not parse_result.extracted_text.strip():
            return self._error_result(
                document_id=document_id,
                status="empty",
                started_at=started_at,
                pages_processed=pages_processed,
                error=IngestionError(
                    code=IngestionErrorCode.EMPTY_DOCUMENT,
                    message="Document contains no extractable text.",
                    detail=f"parser_status={parse_result.status.value}",
                ),
            )

        chunk_metadata: dict[str, Any] = {
            **input_metadata,
            "file_name": filename,
            "content_type": content_type,
            "parser_type": parse_result.parser_type.value,
            "parse_status": parse_result.status.value,
            **parse_result.metadata,
        }

        logger.info("Chunking started: document_id=%s", document_id)

        chunking_result = self._chunker.chunk_text(
            text=parse_result.extracted_text,
            document_id=document_id,
            metadata=chunk_metadata,
        )

        logger.info(
            "Chunking completed: document_id=%s chunks_created=%d",
            document_id,
            chunking_result.total_chunks,
        )

        if chunking_result.total_chunks == 0:
            return self._error_result(
                document_id=document_id,
                status="empty",
                started_at=started_at,
                pages_processed=pages_processed,
                error=IngestionError(
                    code=IngestionErrorCode.EMPTY_DOCUMENT,
                    message="Document produced no chunks after parsing.",
                ),
            )

        logger.info(
            "Embedding started: document_id=%s chunk_count=%d",
            document_id,
            chunking_result.total_chunks,
        )

        try:
            embedding_result = await self._embedder.embed_chunks(chunking_result.chunks)
        except Exception as exc:
            logger.exception("Embedding failed: document_id=%s", document_id)
            return self._error_result(
                document_id=document_id,
                status="embedding_failed",
                started_at=started_at,
                pages_processed=pages_processed,
                chunks_created=chunking_result.total_chunks,
                error=IngestionError(
                    code=IngestionErrorCode.EMBEDDING_FAILED,
                    message="Failed to generate embeddings for document chunks.",
                    detail=str(exc),
                ),
            )

        if not embedding_result.success or not embedding_result.embeddings:
            return self._error_result(
                document_id=document_id,
                status="embedding_failed",
                started_at=started_at,
                pages_processed=pages_processed,
                chunks_created=chunking_result.total_chunks,
                error=IngestionError(
                    code=IngestionErrorCode.EMBEDDING_FAILED,
                    message="Embedding service returned no vectors.",
                ),
            )

        logger.info(
            "Embedding completed: document_id=%s embeddings=%d",
            document_id,
            embedding_result.total_embeddings,
        )

        logger.info("Vector storage started: document_id=%s", document_id)

        try:
            vectors_stored = self._vector_store.upsert_chunks(
                chunks=chunking_result.chunks,
                embeddings=embedding_result.embeddings,
            )
        except QdrantStoreError as exc:
            logger.exception("Vector storage failed: document_id=%s", document_id)
            return self._error_result(
                document_id=document_id,
                status="vector_store_failed",
                started_at=started_at,
                pages_processed=pages_processed,
                chunks_created=chunking_result.total_chunks,
                error=IngestionError(
                    code=IngestionErrorCode.VECTOR_STORE_FAILED,
                    message="Failed to store vectors in Qdrant.",
                    detail=str(exc),
                ),
            )
        except Exception as exc:
            logger.exception("Vector storage failed: document_id=%s", document_id)
            return self._error_result(
                document_id=document_id,
                status="vector_store_failed",
                started_at=started_at,
                pages_processed=pages_processed,
                chunks_created=chunking_result.total_chunks,
                error=IngestionError(
                    code=IngestionErrorCode.VECTOR_STORE_FAILED,
                    message="Unexpected error while storing vectors.",
                    detail=str(exc),
                ),
            )

        logger.info(
            "Vector storage completed: document_id=%s vectors_stored=%d",
            document_id,
            vectors_stored,
        )

        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        return IngestionResult(
            document_id=document_id,
            status="success",
            pages_processed=pages_processed,
            chunks_created=chunking_result.total_chunks,
            vectors_stored=vectors_stored,
            processing_time_ms=elapsed_ms,
        )

    @staticmethod
    def _error_result(
        *,
        document_id: str,
        status: str,
        started_at: float,
        error: IngestionError,
        pages_processed: int = 0,
        chunks_created: int = 0,
        vectors_stored: int = 0,
    ) -> IngestionResult:
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        return IngestionResult(
            document_id=document_id,
            status=status,
            pages_processed=pages_processed,
            chunks_created=chunks_created,
            vectors_stored=vectors_stored,
            processing_time_ms=elapsed_ms,
            error=error,
        )


def _pages_processed(parse_result: ParseResult) -> int:
    page_count = parse_result.metadata.get("page_count")
    if isinstance(page_count, int):
        return page_count
    if parse_result.extracted_text:
        return 1
    return 0


async def ingest_document(
    *,
    document_id: str,
    file_path: str,
    metadata: dict[str, Any] | None = None,
    pipeline: DocumentIngestionPipeline | None = None,
) -> IngestionResult:
    """Run the end-to-end ingestion pipeline for a file on disk."""
    active_pipeline = pipeline or DocumentIngestionPipeline()
    return await active_pipeline.ingest(
        document_id=document_id,
        file_path=file_path,
        metadata=metadata,
    )


async def run_ingestion_pipeline(file: UploadFile) -> UploadIngestionResult:
    """
    Entry point for the upload API ingestion pipeline.

    Validates, stores, and ingests the uploaded file.
    """
    from app.services.ingestion_service import ingest_file

    return await ingest_file(file)
