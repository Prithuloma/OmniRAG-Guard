"""
upload.py
---------
Upload route — accepts multipart file, delegates to ingestion service.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.response_models import UploadIngestionResponse
from app.services.ingestion_service import (
    UploadIngestionErrorCode,
    ingest_file,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/",
    response_model=UploadIngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a document or image for ingestion",
)
async def upload_file(file: UploadFile) -> UploadIngestionResponse:
    """
    Upload endpoint.

    Validates the file, stores it locally, runs the ingestion pipeline,
    and returns an ingestion summary.
    """
    logger.info(f"Received upload request for file: filename={file.filename}, content_type={file.content_type}")
    result = await ingest_file(file)

    if result.status == "validation_failed":
        logger.warning(f"File upload validation failed: filename={file.filename}, detail={result.validation.error if result.validation else 'Unknown'}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.validation.error.model_dump()
            if result.validation and result.validation.error
            else "Validation failed.",
        )

    if result.status == "file_save_failed":
        logger.error(f"File save failed: filename={file.filename}, error={result.error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": UploadIngestionErrorCode.FILE_SAVE_FAILED.value,
                "message": result.error.message if result.error else "Failed to save uploaded file.",
                "detail": result.error.detail if result.error else None,
            },
        )

    if result.status == "ingestion_failed":
        ingestion_status = result.ingestion.status if result.ingestion else "unknown"
        logger.error(f"Document ingestion failed: filename={file.filename}, document_id={result.document_id}, status={ingestion_status}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": UploadIngestionErrorCode.INGESTION_FAILED.value,
                "message": result.error.message if result.error else "Document ingestion failed.",
                "detail": result.error.detail if result.error else None,
                "document_id": result.document_id,
                "ingestion_status": ingestion_status,
            },
        )

    if not result.document_id:
        logger.error(f"Ingestion succeeded but no document ID returned: filename={file.filename}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload completed without a document identifier.",
        )

    logger.info(f"Ingestion completed successfully: filename={file.filename}, document_id={result.document_id}, chunks={result.chunks_created}")
    return UploadIngestionResponse(
        document_id=result.document_id,
        status=result.status,
        chunks_created=result.chunks_created,
        vectors_stored=result.vectors_stored,
        pages_processed=result.ingestion.pages_processed if result.ingestion else 0,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an uploaded document and its vector embeddings",
)
async def delete_document(document_id: str):
    logger.info(f"Received delete request for document_id={document_id}")

    # 1. Delete vectors from Qdrant
    try:
        from app.services.vector_store.qdrant_store import QdrantStore
        store = QdrantStore(vector_dimension=settings.EMBEDDING_DIMENSION)
        store.delete_document(document_id=document_id)
        logger.info(f"Successfully deleted vectors for document_id={document_id} from Qdrant")
    except Exception as exc:
        logger.error(f"Failed to delete Qdrant vectors for document_id={document_id}: {exc}")

    # 2. Delete files from storage
    from pathlib import Path
    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.is_absolute():
        backend_root = Path(__file__).resolve().parents[3]
        upload_dir = backend_root / upload_dir

    deleted_files_count = 0
    for p in upload_dir.glob(f"{document_id}_*"):
        try:
            p.unlink()
            deleted_files_count += 1
            logger.info(f"Deleted file from storage: {p.name}")
        except OSError as exc:
            logger.error(f"Failed to delete file {p.name} from storage: {exc}")

    return {
        "success": True,
        "message": f"Successfully deleted document {document_id} and {deleted_files_count} associated file(s).",
    }
