from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.parsers.base_parser import ParseResult


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    content: str
    index: int


class ChunkingService:
    async def chunk(self, *, parsed: ParseResult) -> list[Chunk]:
        _ = parsed
        # Placeholder chunking — runs after parser.parse()
        return []
