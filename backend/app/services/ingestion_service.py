from __future__ import annotations

from app.models import DocumentStatus, UploadRequest, UploadResponse
from app.services.ingestion.pipeline import IngestionPipeline


class IngestionService:
    def __init__(self, *, pipeline: IngestionPipeline | None = None) -> None:
        self._pipeline = pipeline or IngestionPipeline()

    async def ingest_document(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        request: UploadRequest | None = None,
    ) -> UploadResponse:
        _ = request
        _ = await self._pipeline.run(
            filename=filename,
            content_type=content_type,
            data=data,
        )
        return UploadResponse(
            success=True,
            message="Ingestion accepted (placeholder).",
            filename=filename,
            status=DocumentStatus.PENDING,
        )
