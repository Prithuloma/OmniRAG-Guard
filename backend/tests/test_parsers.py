"""
tests/test_parsers.py
---------------------
Unit tests for parser contracts and placeholder implementations.
"""

from __future__ import annotations

import fitz
import pytest

from app.services.ingestion.parser_dispatcher import ParserDispatcher
from app.services.ingestion.parsers.base_parser import ParseStatus, ParserType
from app.services.ingestion.parsers.image_parser import ImageParser
from app.services.ingestion.parsers.pdf_parser import PDFParser
from app.services.ingestion.parsers.text_parser import TextParser


def _make_pdf_with_text(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def _make_empty_pdf() -> bytes:
    document = fitz.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@pytest.mark.parametrize(
    ("filename", "content_type", "expected_parser_cls", "expected_parser_type"),
    [
        ("annual_report.pdf", "application/pdf", PDFParser, ParserType.PDF),
        ("image.png", "image/png", ImageParser, ParserType.IMAGE),
        ("notes.txt", "text/plain", TextParser, ParserType.TEXT),
        (
            "report.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            TextParser,
            ParserType.TEXT,
        ),
    ],
)
@pytest.mark.asyncio
async def test_dispatcher_returns_correct_parser_instance(
    filename: str,
    content_type: str,
    expected_parser_cls: type,
    expected_parser_type: ParserType,
) -> None:
    dispatcher = ParserDispatcher()
    dispatch_result = await dispatcher.dispatch(
        filename=filename,
        content_type=content_type,
        data=b"",
    )

    assert isinstance(dispatch_result.parser, expected_parser_cls)
    assert dispatch_result.parser_type is expected_parser_type


@pytest.mark.parametrize(
    ("parser_cls", "parser_type", "filename", "content_type"),
    [
        (ImageParser, ParserType.IMAGE, "image.png", "image/png"),
        (TextParser, ParserType.TEXT, "notes.txt", "text/plain"),
        (
            TextParser,
            ParserType.TEXT,
            "report.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ],
)
@pytest.mark.asyncio
async def test_parse_returns_structured_placeholder_result(
    parser_cls: type,
    parser_type: ParserType,
    filename: str,
    content_type: str,
) -> None:
    parser = parser_cls()
    result = await parser.parse(
        filename=filename,
        content_type=content_type,
        data=b"sample-bytes",
    )

    assert result.parser_type is parser_type
    assert result.file_name == filename
    assert result.status is ParseStatus.PLACEHOLDER
    assert result.extracted_text == ""
    assert result.metadata["content_type"] == content_type


@pytest.mark.asyncio
async def test_pdf_parser_extracts_text_from_valid_pdf() -> None:
    parser = PDFParser()
    expected_text = "OmniRAG quarterly report"
    pdf_bytes = _make_pdf_with_text(expected_text)

    result = await parser.parse(
        filename="annual_report.pdf",
        content_type="application/pdf",
        data=pdf_bytes,
    )

    assert result.parser_type is ParserType.PDF
    assert result.file_name == "annual_report.pdf"
    assert result.status is ParseStatus.SUCCESS
    assert expected_text in result.extracted_text
    assert result.metadata["page_count"] == 1
    assert result.metadata["file_name"] == "annual_report.pdf"
    assert result.metadata["parser_type"] == ParserType.PDF.value
    assert result.metadata["extraction_status"] == ParseStatus.SUCCESS.value


@pytest.mark.asyncio
async def test_pdf_parser_handles_empty_pdf() -> None:
    parser = PDFParser()
    pdf_bytes = _make_empty_pdf()

    result = await parser.parse(
        filename="blank.pdf",
        content_type="application/pdf",
        data=pdf_bytes,
    )

    assert result.parser_type is ParserType.PDF
    assert result.status is ParseStatus.EMPTY
    assert result.extracted_text == ""
    assert result.metadata["page_count"] == 1
    assert result.metadata["extraction_status"] == ParseStatus.EMPTY.value


@pytest.mark.asyncio
async def test_pdf_parser_handles_corrupted_pdf() -> None:
    parser = PDFParser()

    result = await parser.parse(
        filename="corrupted.pdf",
        content_type="application/pdf",
        data=b"%PDF-1.4\nthis is not a valid pdf document",
    )

    assert result.parser_type is ParserType.PDF
    assert result.status is ParseStatus.FAILED
    assert result.extracted_text == ""
    assert result.metadata["page_count"] == 0
    assert result.metadata["extraction_status"] == ParseStatus.FAILED.value
