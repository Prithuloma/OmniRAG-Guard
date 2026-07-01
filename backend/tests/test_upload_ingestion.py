"""
tests/test_upload_ingestion.py
------------------------------
Unit tests for upload-to-ingestion wiring.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import fitz
import pytest
from fastapi import UploadFile

from app.services.ingestion.ingestion_pipeline import IngestionError, IngestionErrorCode, IngestionResult
from app.services.ingestion_service import (
    IngestionService,
    UploadIngestionErrorCode,
    ingest_file,
)


def _make_pdf_bytes(text: str = "Upload ingestion wiring test content.") -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def _make_upload_file(
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/pdf",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    target = tmp_path / "uploads"
    target.mkdir()
    return target


@pytest.fixture
def mock_pipeline() -> AsyncMock:
    pipeline = AsyncMock()
    pipeline.ingest.return_value = IngestionResult(
        document_id="doc_test123",
        status="success",
        pages_processed=1,
        chunks_created=2,
        vectors_stored=2,
        processing_time_ms=10.0,
    )
    return pipeline


@pytest.mark.asyncio
async def test_file_saved(
    upload_dir: Path,
    mock_pipeline: AsyncMock,
) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(filename="report.pdf", content=_make_pdf_bytes())

    result = await service.ingest_upload(upload)

    assert result.status == "success"
    assert result.saved_path is not None
    saved_path = Path(result.saved_path)
    assert saved_path.exists()
    assert saved_path.parent == upload_dir
    assert saved_path.name.endswith("_report.pdf")
    assert saved_path.read_bytes().startswith(b"%PDF")


@pytest.mark.asyncio
async def test_ingestion_invoked(
    upload_dir: Path,
    mock_pipeline: AsyncMock,
) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(filename="report.pdf", content=_make_pdf_bytes())

    result = await service.ingest_upload(upload)

    assert result.status == "success"
    mock_pipeline.ingest.assert_awaited_once()
    call_kwargs = mock_pipeline.ingest.await_args.kwargs
    assert call_kwargs["document_id"] == result.document_id
    assert call_kwargs["file_path"] == result.saved_path
    assert call_kwargs["metadata"]["content_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_document_id_returned(
    upload_dir: Path,
    mock_pipeline: AsyncMock,
) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(filename="report.pdf", content=_make_pdf_bytes())

    with patch(
        "app.services.ingestion_service.ingest_document",
        new=AsyncMock(
            return_value=IngestionResult(
                document_id="doc_fixed123",
                status="success",
                pages_processed=1,
                chunks_created=3,
                vectors_stored=3,
                processing_time_ms=8.0,
            )
        ),
    ) as ingest_document_mock:
        result = await service.ingest_upload(upload)

    assert result.status == "success"
    assert result.document_id is not None
    assert result.document_id.startswith("doc_")
    assert result.chunks_created == 3
    assert result.vectors_stored == 3
    ingest_document_mock.assert_awaited_once()
    call_kwargs = ingest_document_mock.await_args.kwargs
    assert call_kwargs["document_id"] == result.document_id
    assert Path(call_kwargs["file_path"]).name == f"{result.document_id}_report.pdf"


@pytest.mark.asyncio
async def test_validation_failure(upload_dir: Path, mock_pipeline: AsyncMock) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(
        filename="notes.exe",
        content=b"invalid",
        content_type="application/octet-stream",
    )

    result = await service.ingest_upload(upload)

    assert result.status == "validation_failed"
    assert result.document_id is None
    assert result.error is not None
    assert result.error.code is UploadIngestionErrorCode.VALIDATION_FAILED
    assert list(upload_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_file_save_failure(upload_dir: Path, mock_pipeline: AsyncMock) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(filename="report.pdf", content=_make_pdf_bytes())

    with patch(
        "app.services.ingestion_service.save_upload_file",
        side_effect=OSError("disk full"),
    ):
        result = await service.ingest_upload(upload)

    assert result.status == "file_save_failed"
    assert result.document_id is not None
    assert result.error is not None
    assert result.error.code is UploadIngestionErrorCode.FILE_SAVE_FAILED
    assert "disk full" in (result.error.detail or "")


@pytest.mark.asyncio
async def test_ingestion_failure(upload_dir: Path, mock_pipeline: AsyncMock) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(filename="report.pdf", content=_make_pdf_bytes())

    with patch(
        "app.services.ingestion_service.ingest_document",
        new=AsyncMock(
            return_value=IngestionResult(
                document_id="doc_fail123",
                status="empty",
                pages_processed=1,
                chunks_created=0,
                vectors_stored=0,
                processing_time_ms=5.0,
                error=IngestionError(
                    code=IngestionErrorCode.EMPTY_DOCUMENT,
                    message="Document contains no extractable text.",
                ),
            )
        ),
    ):
        result = await service.ingest_upload(upload)

    assert result.status == "ingestion_failed"
    assert result.document_id is not None
    assert result.saved_path is not None
    assert Path(result.saved_path).exists()
    assert result.error is not None
    assert result.error.code is UploadIngestionErrorCode.INGESTION_FAILED
    assert result.chunks_created == 0
    assert result.vectors_stored == 0


@pytest.mark.asyncio
async def test_ingest_file_delegates_to_service(mock_pipeline: AsyncMock, upload_dir: Path) -> None:
    service = IngestionService(upload_dir=upload_dir, pipeline=mock_pipeline)
    upload = _make_upload_file(filename="report.pdf", content=_make_pdf_bytes())

    with patch(
        "app.services.ingestion_service.ingest_document",
        new=AsyncMock(
            return_value=IngestionResult(
                document_id="doc_delegate123",
                status="success",
                pages_processed=1,
                chunks_created=1,
                vectors_stored=1,
                processing_time_ms=4.0,
            )
        ),
    ):
        result = await ingest_file(upload, service=service)

    assert result.status == "success"
    assert result.document_id is not None
    assert result.document_id.startswith("doc_")
    assert result.chunks_created == 1
    assert result.vectors_stored == 1
