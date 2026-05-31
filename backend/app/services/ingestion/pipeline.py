from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.chunking import Chunk, ChunkingService
from app.services.ingestion.file_validator import FileValidator, ValidationResult
from app.services.ingestion.parser_dispatcher import (
    ParserDispatchResult,
    ParserDispatcher,
    ParserDispatchStatus,
)


@dataclass(frozen=True, slots=True)
class IngestionPipelineResult:
    validations: list[ValidationResult]
    dispatch: ParserDispatchResult | None
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
        # ------------------------------------------------------------------ #
        # 1. Validate
        # ------------------------------------------------------------------ #
        validations: list[ValidationResult] = [
            self._validator.validate_file_type(content_type=content_type),
            self._validator.validate_file_size(num_bytes=len(data)),
        ]
        if not all(v.ok for v in validations):
            return IngestionPipelineResult(validations=validations, dispatch=None, chunks=[])

        # ------------------------------------------------------------------ #
        # 2. Dispatch parser
        # ------------------------------------------------------------------ #
        dispatch_result = await self._parser.dispatch(
            filename=filename,
            content_type=content_type,
            data=data,
        )

        if dispatch_result.status is not ParserDispatchStatus.SELECTED:
            return IngestionPipelineResult(
                validations=validations,
                dispatch=dispatch_result,
                chunks=[],
            )

        # Future PDF parser — invoked when parser_type == ParserType.PDF
        # Future image parser — invoked when parser_type == ParserType.IMAGE
        # Future text parser — invoked when parser_type == ParserType.TEXT

        # ------------------------------------------------------------------ #
        # 3. Placeholder chunking
        # ------------------------------------------------------------------ #
        chunks = await self._chunker.chunk(dispatch=dispatch_result)
        return IngestionPipelineResult(
            validations=validations,
            dispatch=dispatch_result,
            chunks=chunks,
        )

    async def run(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> IngestionPipelineResult:
        return await self.ingest(filename=filename, content_type=content_type, data=data)
