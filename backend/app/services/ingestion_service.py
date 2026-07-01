"""
ingestion_service.py
--------------------
Service layer — sits between the upload route and the ingestion pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.config import settings
from app.services.ingestion.file_storage import (
    generate_document_id,
    resolve_upload_dir,
    save_upload_file,
)
from app.services.ingestion.file_validator import validate_upload_file
from app.services.ingestion.ingestion_pipeline import (
    DocumentIngestionPipeline,
    IngestionResult,
    ingest_document,
)
from app.services.ingestion.validation import FileValidationResult


class UploadIngestionErrorCode(str, Enum):
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FILE_SAVE_FAILED = "FILE_SAVE_FAILED"
    INGESTION_FAILED = "INGESTION_FAILED"


@dataclass(frozen=True, slots=True)
class UploadIngestionError:
    code: UploadIngestionErrorCode
    message: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class UploadIngestionResult:
    document_id: str | None
    status: str
    chunks_created: int = 0
    vectors_stored: int = 0
    filename: str | None = None
    saved_path: str | None = None
    validation: FileValidationResult | None = None
    ingestion: IngestionResult | None = None
    error: UploadIngestionError | None = None


class IngestionService:
    def __init__(
        self,
        *,
        upload_dir: Path | str | None = None,
        pipeline: DocumentIngestionPipeline | None = None,
    ) -> None:
        self._upload_dir = resolve_upload_dir(upload_dir or settings.UPLOAD_DIR)
        self._pipeline = pipeline or DocumentIngestionPipeline()

    async def ingest_upload(self, file: UploadFile) -> UploadIngestionResult:
        validation_result = await validate_upload_file(file)
        if not validation_result.valid:
            return UploadIngestionResult(
                document_id=None,
                status="validation_failed",
                filename=validation_result.filename,
                validation=validation_result,
                error=UploadIngestionError(
                    code=UploadIngestionErrorCode.VALIDATION_FAILED,
                    message=(
                        validation_result.error.message
                        if validation_result.error
                        else "Uploaded file failed validation."
                    ),
                    detail=validation_result.error.detail if validation_result.error else None,
                ),
            )

        filename = validation_result.filename
        if not filename:
            return UploadIngestionResult(
                document_id=None,
                status="validation_failed",
                validation=validation_result,
                error=UploadIngestionError(
                    code=UploadIngestionErrorCode.VALIDATION_FAILED,
                    message="Uploaded file has no filename.",
                ),
            )

        document_id = generate_document_id()
        content = await file.read()

        try:
            saved_path = save_upload_file(
                upload_dir=self._upload_dir,
                document_id=document_id,
                original_filename=filename,
                content=content,
            )
        except OSError as exc:
            return UploadIngestionResult(
                document_id=document_id,
                status="file_save_failed",
                filename=filename,
                validation=validation_result,
                error=UploadIngestionError(
                    code=UploadIngestionErrorCode.FILE_SAVE_FAILED,
                    message="Failed to save uploaded file.",
                    detail=str(exc),
                ),
            )

        metadata: dict[str, Any] = {}
        if validation_result.detected_mime:
            metadata["content_type"] = validation_result.detected_mime

        ingestion_result = await ingest_document(
            document_id=document_id,
            file_path=str(saved_path),
            metadata=metadata,
            pipeline=self._pipeline,
        )

        if ingestion_result.status != "success":
            return UploadIngestionResult(
                document_id=document_id,
                status="ingestion_failed",
                filename=filename,
                saved_path=str(saved_path),
                validation=validation_result,
                ingestion=ingestion_result,
                error=UploadIngestionError(
                    code=UploadIngestionErrorCode.INGESTION_FAILED,
                    message=(
                        ingestion_result.error.message
                        if ingestion_result.error
                        else "Document ingestion failed."
                    ),
                    detail=ingestion_result.error.detail if ingestion_result.error else None,
                ),
            )

        return UploadIngestionResult(
            document_id=document_id,
            status="success",
            chunks_created=ingestion_result.chunks_created,
            vectors_stored=ingestion_result.vectors_stored,
            filename=filename,
            saved_path=str(saved_path),
            validation=validation_result,
            ingestion=ingestion_result,
        )


async def ingest_file(
    file: UploadFile,
    *,
    service: IngestionService | None = None,
) -> UploadIngestionResult:
    """
    Orchestrate upload validation, local storage, and document ingestion.

    Returns a structured result; callers map failures to HTTP responses.
    """
    active_service = service or IngestionService()
    return await active_service.ingest_upload(file)
