from __future__ import annotations

from app.services.ingestion.parsers.base_parser import (
    BaseParser,
    ParseResult,
    ParseStatus,
    ParserType,
)


class ImageParser(BaseParser):
    async def parse(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParseResult:
        _ = data
        return ParseResult(
            parser_type=ParserType.IMAGE,
            file_name=filename,
            status=ParseStatus.PLACEHOLDER,
            extracted_text="",
            metadata={"content_type": content_type},
        )
