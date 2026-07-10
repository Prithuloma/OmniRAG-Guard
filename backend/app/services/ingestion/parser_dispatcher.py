from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.ingestion.parsers.base_parser import BaseParser, ParserType
from app.services.ingestion.parsers.docx_parser import DocxParser
from app.services.ingestion.parsers.image_parser import ImageParser
from app.services.ingestion.parsers.pdf_parser import PDFParser
from app.services.ingestion.parsers.text_parser import TextParser


class ParserDispatchStatus(str, Enum):
    SELECTED = "selected"
    UNSUPPORTED = "unsupported"


_EXTENSION_TO_PARSER: dict[str, ParserType] = {
    ".pdf": ParserType.PDF,
    ".png": ParserType.IMAGE,
    ".jpg": ParserType.IMAGE,
    ".jpeg": ParserType.IMAGE,
    ".txt": ParserType.TEXT,
    ".docx": ParserType.DOCX,
}

_PARSER_FACTORY: dict[ParserType, type[BaseParser]] = {
    ParserType.PDF: PDFParser,
    ParserType.IMAGE: ImageParser,
    ParserType.TEXT: TextParser,
    ParserType.DOCX: DocxParser,
}


def select_parser_type(extension: str) -> ParserType | None:
    """Return the parser modality for a normalized file extension, or None."""
    return _EXTENSION_TO_PARSER.get(extension.lower())


def create_parser(parser_type: ParserType) -> BaseParser:
    """Instantiate the parser implementation for the given modality."""
    return _PARSER_FACTORY[parser_type]()


@dataclass(frozen=True, slots=True)
class ParserDispatchResult:
    parser_type: ParserType | None
    file_name: str
    file_extension: str
    status: ParserDispatchStatus
    parser: BaseParser | None
    metadata: dict[str, Any] = field(default_factory=dict)


class ParserDispatcher:
    async def dispatch(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParserDispatchResult:
        """
        Inspect file extension and return a parser selection result.

        Does not parse file content.
        """
        _ = data  # reserved for future parser implementations

        file_extension = os.path.splitext(filename)[1].lower()
        parser_type = select_parser_type(file_extension)
        metadata: dict[str, Any] = {"content_type": content_type}

        if parser_type is None:
            return ParserDispatchResult(
                parser_type=None,
                file_name=filename,
                file_extension=file_extension,
                status=ParserDispatchStatus.UNSUPPORTED,
                parser=None,
                metadata=metadata,
            )

        return ParserDispatchResult(
            parser_type=parser_type,
            file_name=filename,
            file_extension=file_extension,
            status=ParserDispatchStatus.SELECTED,
            parser=create_parser(parser_type),
            metadata=metadata,
        )
