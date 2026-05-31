from __future__ import annotations

import fitz

from app.services.ingestion.parsers.base_parser import (
    BaseParser,
    ParseResult,
    ParseStatus,
    ParserType,
)


class PDFParser(BaseParser):
    async def parse(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParseResult:
        if not data:
            return self._build_result(
                filename=filename,
                content_type=content_type,
                status=ParseStatus.EMPTY,
                extracted_text="",
                page_count=0,
            )

        try:
            with fitz.open(stream=data, filetype="pdf") as document:
                page_count = document.page_count
                if page_count == 0:
                    return self._build_result(
                        filename=filename,
                        content_type=content_type,
                        status=ParseStatus.EMPTY,
                        extracted_text="",
                        page_count=0,
                    )

                page_texts: list[str] = []
                for page in document:
                    page_texts.append(page.get_text())

                extracted_text = "\n".join(page_texts).strip()
                if not extracted_text:
                    return self._build_result(
                        filename=filename,
                        content_type=content_type,
                        status=ParseStatus.EMPTY,
                        extracted_text="",
                        page_count=page_count,
                    )

                return self._build_result(
                    filename=filename,
                    content_type=content_type,
                    status=ParseStatus.SUCCESS,
                    extracted_text=extracted_text,
                    page_count=page_count,
                )
        except Exception:
            return self._build_result(
                filename=filename,
                content_type=content_type,
                status=ParseStatus.FAILED,
                extracted_text="",
                page_count=0,
            )

    def _build_result(
        self,
        *,
        filename: str,
        content_type: str,
        status: ParseStatus,
        extracted_text: str,
        page_count: int,
    ) -> ParseResult:
        return ParseResult(
            parser_type=ParserType.PDF,
            file_name=filename,
            status=status,
            extracted_text=extracted_text,
            metadata={
                "content_type": content_type,
                "page_count": page_count,
                "file_name": filename,
                "parser_type": ParserType.PDF.value,
                "extraction_status": status.value,
            },
        )
