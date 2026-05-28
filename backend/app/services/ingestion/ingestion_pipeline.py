"""
ingestion_pipeline.py
---------------------
Ingestion pipeline scaffold.

Phase B Step 1: validation gate only.
Parsing / embedding / Qdrant NOT implemented yet.
"""

from __future__ import annotations

from fastapi import UploadFile

from app.services.ingestion.validation import FileValidationResult
from app.services.ingestion.file_validator import validate_upload_file


async def run_ingestion_pipeline(file: UploadFile) -> FileValidationResult:
    """
    Entry point for the ingestion pipeline.

    Currently executes the validation gate only.
    Returns FileValidationResult; pipeline aborts on invalid files.
    """
    validation_result: FileValidationResult = await validate_upload_file(file)
    return validation_result
