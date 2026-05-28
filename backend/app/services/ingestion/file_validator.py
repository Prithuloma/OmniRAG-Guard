"""
file_validator.py
-----------------
Production-grade, async-friendly file validation.

Validates:
  - MIME type (declared + magic-byte sniff)
  - File extension
  - File size

Does NOT parse, embed, or process file content.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from fastapi import UploadFile

from app.core.constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_UPLOAD_SIZE_BYTES,
)
from app.services.ingestion.validation import (
    FileValidationResult,
    ValidationError,
    ValidationErrorCode,
)

# ---------------------------------------------------------------------------
# Minimal, interface-first validator API (used by placeholder pipeline scaffolds)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    error: str | None = None


class FileValidator:
    def validate_file_type(self, *, content_type: str) -> ValidationResult:
        if content_type not in ALLOWED_MIME_TYPES:
            return ValidationResult(ok=False, error="unsupported_file_type")
        return ValidationResult(ok=True)

    def validate_file_size(self, *, num_bytes: int) -> ValidationResult:
        if num_bytes < 0:
            return ValidationResult(ok=False, error="invalid_file_size")
        if num_bytes > MAX_UPLOAD_SIZE_BYTES:
            return ValidationResult(ok=False, error="file_too_large")
        return ValidationResult(ok=True)

# ---------------------------------------------------------------------------
# Magic-byte signatures for server-side MIME sniffing
# ---------------------------------------------------------------------------
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF", "application/pdf"),
    (b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
]
_MAGIC_READ_BYTES: int = 16


def _sniff_mime(header: bytes) -> Optional[str]:
    """Return a MIME type string if the header matches a known magic signature."""
    for signature, mime in _MAGIC_SIGNATURES:
        if header.startswith(signature):
            return mime
    return None


def _is_likely_text(header: bytes) -> bool:
    """Heuristic: treat as text/plain if the first bytes are all printable ASCII / UTF-8."""
    try:
        header.decode("utf-8")
        return True
    except (UnicodeDecodeError, ValueError):
        return False


async def validate_upload_file(file: UploadFile) -> FileValidationResult:
    """
    Validate an incoming UploadFile.

    Returns a FileValidationResult; never raises — callers inspect `.valid`.
    """
    # ------------------------------------------------------------------ #
    # 1. Filename presence
    # ------------------------------------------------------------------ #
    filename: Optional[str] = file.filename
    if not filename:
        return FileValidationResult(
            valid=False,
            error=ValidationError(
                code=ValidationErrorCode.MISSING_FILENAME,
                message="Uploaded file has no filename.",
            ),
        )

    # ------------------------------------------------------------------ #
    # 2. Extension check
    # ------------------------------------------------------------------ #
    ext: str = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return FileValidationResult(
            valid=False,
            filename=filename,
            error=ValidationError(
                code=ValidationErrorCode.UNSUPPORTED_TYPE,
                message=f"File extension '{ext}' is not supported.",
                detail=f"Allowed extensions: {sorted(ALLOWED_EXTENSIONS)}",
            ),
        )

    # ------------------------------------------------------------------ #
    # 3. Read file into memory for size + magic-byte checks
    # ------------------------------------------------------------------ #
    content: bytes = await file.read()
    await file.seek(0)  # reset so downstream consumers can re-read

    file_size: int = len(content)

    # ------------------------------------------------------------------ #
    # 4. File size check
    # ------------------------------------------------------------------ #
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        max_mb: float = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        actual_mb: float = file_size / (1024 * 1024)
        return FileValidationResult(
            valid=False,
            filename=filename,
            file_size_bytes=file_size,
            error=ValidationError(
                code=ValidationErrorCode.FILE_TOO_LARGE,
                message=f"File size {actual_mb:.2f} MB exceeds the {max_mb:.0f} MB limit.",
                detail=f"Received {file_size} bytes; maximum is {MAX_UPLOAD_SIZE_BYTES} bytes.",
            ),
        )

    # ------------------------------------------------------------------ #
    # 5. MIME / magic-byte detection
    # ------------------------------------------------------------------ #
    header: bytes = content[:_MAGIC_READ_BYTES]
    detected_mime: Optional[str] = _sniff_mime(header)

    # Fall back to text/plain heuristic for .txt files
    if detected_mime is None and ext == ".txt" and _is_likely_text(header):
        detected_mime = "text/plain"

    # Use declared content_type as last resort when sniffing is inconclusive
    # (e.g. empty files in tests)
    effective_mime: Optional[str] = detected_mime or file.content_type

    if effective_mime not in ALLOWED_MIME_TYPES:
        return FileValidationResult(
            valid=False,
            filename=filename,
            file_size_bytes=file_size,
            detected_mime=effective_mime,
            error=ValidationError(
                code=ValidationErrorCode.UNSUPPORTED_TYPE,
                message=f"MIME type '{effective_mime}' is not supported.",
                detail=f"Allowed types: {list(ALLOWED_MIME_TYPES.keys())}",
            ),
        )

    # ------------------------------------------------------------------ #
    # 6. Extension / MIME consistency check
    # ------------------------------------------------------------------ #
    _EXT_TO_MIME: dict[str, str] = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    expected_mime: Optional[str] = _EXT_TO_MIME.get(ext)
    if expected_mime and effective_mime != expected_mime:
        return FileValidationResult(
            valid=False,
            filename=filename,
            file_size_bytes=file_size,
            detected_mime=effective_mime,
            error=ValidationError(
                code=ValidationErrorCode.EXTENSION_MISMATCH,
                message=(
                    f"File extension '{ext}' does not match detected MIME type "
                    f"'{effective_mime}'."
                ),
                detail=f"Expected MIME for '{ext}': '{expected_mime}'.",
            ),
        )

    # ------------------------------------------------------------------ #
    # 7. All checks passed
    # ------------------------------------------------------------------ #
    return FileValidationResult(
        valid=True,
        filename=filename,
        detected_mime=effective_mime,
        file_size_bytes=file_size,
    )
