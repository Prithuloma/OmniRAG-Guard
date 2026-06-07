"""
upload.py
---------
Upload route — accepts multipart file, delegates to ingestion service.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.models.response_models import UploadIngestionResponse
from app.services.ingestion_service import (
    UploadIngestionErrorCode,
    ingest_file,
)

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
    result = await ingest_file(file)

    if result.status == "validation_failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.validation.error.model_dump()
            if result.validation and result.validation.error
            else "Validation failed.",
        )

    if result.status == "file_save_failed":
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload completed without a document identifier.",
        )

    return UploadIngestionResponse(
        document_id=result.document_id,
        status=result.status,
        chunks_created=result.chunks_created,
        vectors_stored=result.vectors_stored,
    )
