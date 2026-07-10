from __future__ import annotations

from app.services.ingestion.parsers.base_parser import (
    BaseParser,
    ParseResult,
    ParseStatus,
    ParserType,
)


class TextParser(BaseParser):
    async def parse(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParseResult:
        try:
            text = data.decode("utf-8")
            status = ParseStatus.SUCCESS if text.strip() else ParseStatus.EMPTY
            return ParseResult(
                parser_type=ParserType.TEXT,
                file_name=filename,
                status=status,
                extracted_text=text,
                metadata={
                    "content_type": content_type,
                    "file_name": filename,
                    "parser_type": ParserType.TEXT.value,
                    "extraction_status": status.value,
                },
            )
        except Exception as exc:
            return ParseResult(
                parser_type=ParserType.TEXT,
                file_name=filename,
                status=ParseStatus.FAILED,
                extracted_text="",
                metadata={
                    "content_type": content_type,
                    "error": str(exc),
                    "parser_type": ParserType.TEXT.value,
                    "extraction_status": ParseStatus.FAILED.value,
                },
            )
