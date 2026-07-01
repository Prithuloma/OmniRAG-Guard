from __future__ import annotations

from app.services.ingestion.parsers.base_parser import (
    BaseParser,
    ParseResult,
    ParseStatus,
    ParserType,
)


import io
from PIL import Image
import pytesseract

class ImageParser(BaseParser):
    async def parse(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ParseResult:
        try:
            image = Image.open(io.BytesIO(data))
            
            try:
                extracted_text = pytesseract.image_to_string(image)
                status = ParseStatus.SUCCESS if extracted_text.strip() else ParseStatus.EMPTY
            except pytesseract.TesseractNotFoundError:
                # Graceful fallback if tesseract binary is not installed on system
                extracted_text = f"[OCR Fallback: Tesseract binary not installed on host]"
                status = ParseStatus.PLACEHOLDER
            
            return ParseResult(
                parser_type=ParserType.IMAGE,
                file_name=filename,
                status=status,
                extracted_text=extracted_text,
                metadata={
                    "content_type": content_type,
                    "file_name": filename,
                    "parser_type": ParserType.IMAGE.value,
                    "extraction_status": status.value,
                    "image_format": image.format,
                    "image_size": image.size,
                },
            )
        except Exception as exc:
            return ParseResult(
                parser_type=ParserType.IMAGE,
                file_name=filename,
                status=ParseStatus.FAILED,
                extracted_text="",
                metadata={
                    "content_type": content_type,
                    "error": str(exc),
                    "parser_type": ParserType.IMAGE.value,
                    "extraction_status": ParseStatus.FAILED.value,
                },
            )
