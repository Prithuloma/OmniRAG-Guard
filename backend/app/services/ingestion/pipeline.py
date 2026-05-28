from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.chunking import Chunk, ChunkingService
from app.services.ingestion.file_validator import FileValidator, ValidationResult
from app.services.ingestion.parser_dispatcher import ParsedDocument, ParserDispatcher


@dataclass(frozen=True, slots=True)
class IngestionPipelineResult:
    validations: list[ValidationResult]
    parsed: ParsedDocument | None
    chunks: list[Chunk]


class IngestionPipeline:
    def __init__(
        self,
        *,
        validator: FileValidator | None = None,
        parser: ParserDispatcher | None = None,
        chunker: ChunkingService | None = None,
    ) -> None:
        self._validator = validator or FileValidator()
        self._parser = parser or ParserDispatcher()
        self._chunker = chunker or ChunkingService()

    async def ingest(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> IngestionPipelineResult:
        validations: list[ValidationResult] = [
            self._validator.validate_file_type(content_type=content_type),
            self._validator.validate_file_size(num_bytes=len(data)),
        ]
        if not all(v.ok for v in validations):
            return IngestionPipelineResult(validations=validations, parsed=None, chunks=[])

        parsed = await self._parser.parse(
            filename=filename,
            content_type=content_type,
            data=data,
        )
        chunks = await self._chunker.chunk(document=parsed)
        return IngestionPipelineResult(validations=validations, parsed=parsed, chunks=chunks)

    async def run(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> IngestionPipelineResult:
        return await self.ingest(filename=filename, content_type=content_type, data=data)

