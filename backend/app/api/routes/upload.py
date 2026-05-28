"""
upload.py
---------
Upload route — accepts multipart file, delegates to ingestion service.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.services.ingestion.validation import FileValidationResult
from app.services.ingestion_service import ingest_file

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/",
    response_model=FileValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Upload a document or image for ingestion",
)
async def upload_file(file: UploadFile) -> FileValidationResult:
    """
    Upload endpoint.

    Validates the file and returns a structured result.
    Returns HTTP 422 when validation fails so clients receive a consistent
    error shape without a 500.
    """
    result: FileValidationResult = await ingest_file(file)

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.error.model_dump() if result.error else "Validation failed.",
        )

    return result
