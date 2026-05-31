from __future__ import annotations

from typing import Any

from app.services.chunking.chunk_models import Chunk, ChunkingResult


class TextChunker:
    def __init__(self, *, chunk_size: int = 1000, overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")

        self._chunk_size = chunk_size
        self._overlap = overlap
        self._step = chunk_size - overlap

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def overlap(self) -> int:
        return self._overlap

    def chunk_text(
        self,
        *,
        text: str,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChunkingResult:
        base_metadata: dict[str, Any] = dict(metadata or {})

        if not text:
            return ChunkingResult(success=True, total_chunks=0, chunks=[])

        text_length = len(text)
        if text_length <= self._chunk_size:
            chunk = self._build_chunk(
                text=text,
                document_id=document_id,
                chunk_index=0,
                start_char=0,
                end_char=text_length,
                base_metadata=base_metadata,
            )
            return ChunkingResult(success=True, total_chunks=1, chunks=[chunk])

        chunks: list[Chunk] = []
        start_char = 0
        chunk_index = 0

        while start_char < text_length:
            end_char = min(start_char + self._chunk_size, text_length)
            chunks.append(
                self._build_chunk(
                    text=text,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=end_char,
                    base_metadata=base_metadata,
                )
            )

            if end_char >= text_length:
                break

            start_char += self._step
            chunk_index += 1

        return ChunkingResult(success=True, total_chunks=len(chunks), chunks=chunks)

    def _build_chunk(
        self,
        *,
        text: str,
        document_id: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
        base_metadata: dict[str, Any],
    ) -> Chunk:
        chunk_metadata = {
            **base_metadata,
            "document_id": document_id,
            "chunk_index": chunk_index,
            "start_char": start_char,
            "end_char": end_char,
            "char_count": end_char - start_char,
        }
        return Chunk(
            chunk_id=f"{document_id}:chunk:{chunk_index}",
            document_id=document_id,
            content=text[start_char:end_char],
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata=chunk_metadata,
        )
