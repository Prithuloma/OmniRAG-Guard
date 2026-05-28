from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ValidationErrorCode(str, Enum):
    UNSUPPORTED_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    MISSING_FILENAME = "MISSING_FILENAME"
    EXTENSION_MISMATCH = "EXTENSION_MISMATCH"


class ValidationError(BaseModel):
    code: ValidationErrorCode
    message: str
    detail: Optional[str] = Field(default=None)


class FileValidationResult(BaseModel):
    valid: bool
    filename: Optional[str] = Field(default=None)
    detected_mime: Optional[str] = Field(default=None)
    file_size_bytes: Optional[int] = Field(default=None)
    error: Optional[ValidationError] = Field(default=None)
