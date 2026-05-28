"""
ingestion_service.py
--------------------
Service layer — sits between the upload route and the ingestion pipeline.
"""

from __future__ import annotations

from fastapi import UploadFile

from app.services.ingestion.validation import FileValidationResult
from app.services.ingestion.ingestion_pipeline import run_ingestion_pipeline


async def ingest_file(file: UploadFile) -> FileValidationResult:
    """
    Orchestrate file ingestion.

    Delegates to the pipeline; returns a FileValidationResult.
    Raises no exceptions — structured errors live inside the result.
    """
    return await run_ingestion_pipeline(file)
