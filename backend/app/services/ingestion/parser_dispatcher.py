from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Parser modality taxonomy
# ---------------------------------------------------------------------------


class ParserType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"


class ParserDispatchStatus(str, Enum):
    SELECTED = "selected"
    UNSUPPORTED = "unsupported"


# ---------------------------------------------------------------------------
# Extension → parser routing table
# ---------------------------------------------------------------------------

_EXTENSION_TO_PARSER: dict[str, ParserType] = {
    ".pdf": ParserType.PDF,
    ".png": ParserType.IMAGE,
    ".jpg": ParserType.IMAGE,
    ".jpeg": ParserType.IMAGE,
    ".txt": ParserType.TEXT,
    ".docx": ParserType.TEXT,
}


def select_parser_type(extension: str) -> ParserType | None:
    """Return the parser modality for a normalized file extension, or None."""
    return _EXTENSION_TO_PARSER.get(extension.lower())


# ---------------------------------------------------------------------------
# Dispatch result model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParserDispatchResult:
    parser_type: ParserType | None
    file_name: str
    file_extension: str
    status: ParserDispatchStatus
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parser dispatcher — routing only, no parsing
# ---------------------------------------------------------------------------


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
                metadata=metadata,
            )

        return ParserDispatchResult(
            parser_type=parser_type,
            file_name=filename,
            file_extension=file_extension,
            status=ParserDispatchStatus.SELECTED,
            metadata=metadata,
        )
