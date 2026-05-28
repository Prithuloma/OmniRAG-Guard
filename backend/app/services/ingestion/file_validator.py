from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    error: str | None = None


class FileValidator:
    def __init__(
        self,
        *,
        allowed_content_types: Iterable[str] = ("application/pdf", "image/png", "image/jpeg"),
        max_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        self._allowed_content_types = set(allowed_content_types)
        self._max_bytes = max_bytes

    def validate_file_type(self, *, content_type: str) -> ValidationResult:
        if content_type not in self._allowed_content_types:
            return ValidationResult(ok=False, error="unsupported_file_type")
        return ValidationResult(ok=True)

    def validate_file_size(self, *, num_bytes: int) -> ValidationResult:
        if num_bytes < 0:
            return ValidationResult(ok=False, error="invalid_file_size")
        if num_bytes > self._max_bytes:
            return ValidationResult(ok=False, error="file_too_large")
        return ValidationResult(ok=True)

