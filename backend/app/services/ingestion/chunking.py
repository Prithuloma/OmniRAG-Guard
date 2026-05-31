from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.parser_dispatcher import ParserDispatchResult


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    content: str
    index: int


class ChunkingService:
    async def chunk(self, *, dispatch: ParserDispatchResult) -> list[Chunk]:
        _ = dispatch
        # Placeholder chunking — runs after parser dispatch selection
        return []
