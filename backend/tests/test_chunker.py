"""
tests/test_chunker.py
---------------------
Unit tests for text chunking.
"""

from __future__ import annotations

import pytest

from app.services.chunking.text_chunker import TextChunker


@pytest.fixture
def chunker() -> TextChunker:
    return TextChunker(chunk_size=1000, overlap=200)


def test_chunk_empty_text(chunker: TextChunker) -> None:
    result = chunker.chunk_text(text="", document_id="doc-empty")

    assert result.success is True
    assert result.total_chunks == 0
    assert result.chunks == []


def test_chunk_short_text(chunker: TextChunker) -> None:
    text = "Short document body."
    result = chunker.chunk_text(text=text, document_id="doc-short")

    assert result.success is True
    assert result.total_chunks == 1
    assert len(result.chunks) == 1

    chunk = result.chunks[0]
    assert chunk.chunk_index == 0
    assert chunk.start_char == 0
    assert chunk.end_char == len(text)
    assert chunk.content == text
    assert chunk.document_id == "doc-short"
    assert chunk.chunk_id == "doc-short:chunk:0"


def test_chunk_multi_chunk_document(chunker: TextChunker) -> None:
    text = "a" * 2500
    result = chunker.chunk_text(text=text, document_id="doc-large")

    assert result.success is True
    assert result.total_chunks == 3
    assert len(result.chunks) == 3
    assert result.chunks[0].start_char == 0
    assert result.chunks[0].end_char == 1000
    assert result.chunks[1].start_char == 800
    assert result.chunks[1].end_char == 1800
    assert result.chunks[2].start_char == 1600
    assert result.chunks[2].end_char == 2500


def test_chunk_overlap_correctness(chunker: TextChunker) -> None:
    text = "abcdefghijklmnopqrstuvwxyz" * 100
    result = chunker.chunk_text(text=text, document_id="doc-overlap")

    for index in range(1, len(result.chunks)):
        previous = result.chunks[index - 1]
        current = result.chunks[index]
        assert previous.content[-200:] == current.content[:200]


def test_chunk_ordering(chunker: TextChunker) -> None:
    text = "word " * 600
    result = chunker.chunk_text(text=text, document_id="doc-order")

    assert [chunk.chunk_index for chunk in result.chunks] == list(
        range(len(result.chunks))
    )
    for chunk in result.chunks:
        assert chunk.content == text[chunk.start_char : chunk.end_char]


def test_chunk_very_large_text() -> None:
    chunker = TextChunker(chunk_size=1000, overlap=200)
    text = "x" * 50_000
    result = chunker.chunk_text(text=text, document_id="doc-xl")

    assert result.success is True
    assert result.total_chunks == len(result.chunks)
    assert result.chunks[0].chunk_index == 0
    assert result.chunks[-1].end_char == len(text)
    assert all(chunk.document_id == "doc-xl" for chunk in result.chunks)
