from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    content_type: str
    text: str
    metadata: dict[str, Any]


class ParserDispatcher:
    async def parse(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParsedDocument:
        _ = filename
        _ = data
        return ParsedDocument(
            content_type=content_type,
            text="",
            metadata={},
        )

