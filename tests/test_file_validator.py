"""
tests/test_file_validator.py
----------------------------
Unit tests for the file validation layer.
"""

from __future__ import annotations

import io
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.constants import MAX_UPLOAD_SIZE_BYTES
from app.services.ingestion.validation import ValidationErrorCode
from app.services.ingestion.file_validator import validate_upload_file


def _make_upload_file(
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> MagicMock:
    mock = MagicMock()
    mock.filename = filename
    mock.content_type = content_type
    _buf = io.BytesIO(content)

    async def _read() -> bytes:
        return _buf.read()

    async def _seek(pos: int) -> None:
        _buf.seek(pos)

    mock.read = _read
    mock.seek = _seek
    return mock


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_valid_pdf():
    content = b"%PDF-1.4 fake pdf body"
    f = _make_upload_file("report.pdf", content, "application/pdf")
    result = await validate_upload_file(f)
    assert result.valid is True
    assert result.detected_mime == "application/pdf"


@pytest.mark.asyncio
async def test_valid_txt():
    content = b"Hello world"
    f = _make_upload_file("notes.txt", content, "text/plain")
    result = await validate_upload_file(f)
    assert result.valid is True
    assert result.detected_mime == "text/plain"


@pytest.mark.asyncio
async def test_valid_png():
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    f = _make_upload_file("image.png", content, "image/png")
    result = await validate_upload_file(f)
    assert result.valid is True


@pytest.mark.asyncio
async def test_valid_jpeg():
    content = b"\xff\xd8\xff" + b"\x00" * 100
    f = _make_upload_file("photo.jpg", content, "image/jpeg")
    result = await validate_upload_file(f)
    assert result.valid is True


@pytest.mark.asyncio
async def test_valid_docx():
    content = b"PK\x03\x04" + b"\x00" * 100
    f = _make_upload_file("doc.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    result = await validate_upload_file(f)
    assert result.valid is True


# ---------------------------------------------------------------------------
# Rejection tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_filename():
    f = _make_upload_file("", b"data")
    f.filename = ""
    result = await validate_upload_file(f)
    assert result.valid is False
    assert result.error.code == ValidationErrorCode.MISSING_FILENAME


@pytest.mark.asyncio
async def test_unsupported_extension():
    f = _make_upload_file("script.exe", b"MZ\x90\x00")
    result = await validate_upload_file(f)
    assert result.valid is False
    assert result.error.code == ValidationErrorCode.UNSUPPORTED_TYPE


@pytest.mark.asyncio
async def test_file_too_large():
    oversized = b"%PDF" + b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)
    f = _make_upload_file("big.pdf", oversized, "application/pdf")
    result = await validate_upload_file(f)
    assert result.valid is False
    assert result.error.code == ValidationErrorCode.FILE_TOO_LARGE


@pytest.mark.asyncio
async def test_extension_mime_mismatch():
    # .pdf extension but PNG magic bytes
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    f = _make_upload_file("fake.pdf", content, "image/png")
    result = await validate_upload_file(f)
    assert result.valid is False
    assert result.error.code == ValidationErrorCode.EXTENSION_MISMATCH
