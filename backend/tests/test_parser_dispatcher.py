"""
tests/test_parser_dispatcher.py
--------------------------------
Unit tests for parser dispatch routing (selection only, no parsing).
"""

from __future__ import annotations

import pytest

from app.services.ingestion.parser_dispatcher import (
    ParserDispatchStatus,
    ParserDispatcher,
)
from app.services.ingestion.parsers.base_parser import BaseParser, ParserType
from app.services.ingestion.parsers.image_parser import ImageParser
from app.services.ingestion.parsers.pdf_parser import PDFParser
from app.services.ingestion.parsers.text_parser import TextParser


@pytest.fixture
def dispatcher() -> ParserDispatcher:
    return ParserDispatcher()


@pytest.mark.parametrize(
    (
        "filename",
        "content_type",
        "expected_parser_type",
        "expected_extension",
        "expected_parser_cls",
    ),
    [
        (
            "annual_report.pdf",
            "application/pdf",
            ParserType.PDF,
            ".pdf",
            PDFParser,
        ),
        (
            "image.png",
            "image/png",
            ParserType.IMAGE,
            ".png",
            ImageParser,
        ),
        (
            "photo.jpg",
            "image/jpeg",
            ParserType.IMAGE,
            ".jpg",
            ImageParser,
        ),
        (
            "notes.txt",
            "text/plain",
            ParserType.TEXT,
            ".txt",
            TextParser,
        ),
        (
            "report.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ParserType.TEXT,
            ".docx",
            TextParser,
        ),
    ],
)
@pytest.mark.asyncio
async def test_dispatch_selects_parser_by_extension(
    dispatcher: ParserDispatcher,
    filename: str,
    content_type: str,
    expected_parser_type: ParserType,
    expected_extension: str,
    expected_parser_cls: type[BaseParser],
) -> None:
    result = await dispatcher.dispatch(
        filename=filename,
        content_type=content_type,
        data=b"",
    )

    assert result.parser_type is expected_parser_type
    assert result.status is ParserDispatchStatus.SELECTED
    assert result.file_name == filename
    assert result.file_extension == expected_extension
    assert result.metadata["content_type"] == content_type
    assert isinstance(result.parser, expected_parser_cls)
