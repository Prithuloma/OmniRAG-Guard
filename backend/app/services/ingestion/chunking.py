from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.parser_dispatcher import ParsedDocument


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    content: str
    index: int


class ChunkingService:
    async def chunk(self, *, document: ParsedDocument) -> list[Chunk]:
        _ = document
        return []

