from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParserType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"


class ParseStatus(str, Enum):
    PLACEHOLDER = "placeholder"
    SUCCESS = "success"
    EMPTY = "empty"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ParseResult:
    parser_type: ParserType
    file_name: str
    status: ParseStatus
    extracted_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    @abstractmethod
    async def parse(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParseResult:
        """Parse file content and return structured extraction result."""
