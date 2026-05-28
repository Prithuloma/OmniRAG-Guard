from __future__ import annotations

from app.models import DocumentStatus, UploadRequest, UploadResponse


class IngestionService:
    async def ingest_document(
        self,
        *,
        filename: str,
        request: UploadRequest | None = None,
    ) -> UploadResponse:
        _ = request
        return UploadResponse(
            success=True,
            message="Ingestion accepted (service scaffold).",
            filename=filename,
            status=DocumentStatus.PENDING,
        )
