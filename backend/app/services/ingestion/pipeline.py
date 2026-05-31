from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.chunking import Chunk, ChunkingService
from app.services.ingestion.file_validator import FileValidator, ValidationResult
from app.services.ingestion.parser_dispatcher import (
    ParserDispatchResult,
    ParserDispatcher,
    ParserDispatchStatus,
)
from app.services.ingestion.parsers.base_parser import ParseResult


@dataclass(frozen=True, slots=True)
class IngestionPipelineResult:
    validations: list[ValidationResult]
    dispatch: ParserDispatchResult | None
    parsed: ParseResult | None
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
            return IngestionPipelineResult(
                validations=validations,
                dispatch=None,
                parsed=None,
                chunks=[],
            )

        # ------------------------------------------------------------------ #
        # 2. Dispatch parser
        # ------------------------------------------------------------------ #
        dispatch_result = await self._parser.dispatch(
            filename=filename,
            content_type=content_type,
            data=data,
        )

        if (
            dispatch_result.status is not ParserDispatchStatus.SELECTED
            or dispatch_result.parser is None
        ):
            return IngestionPipelineResult(
                validations=validations,
                dispatch=dispatch_result,
                parsed=None,
                chunks=[],
            )

        # ------------------------------------------------------------------ #
        # 3. Parse
        # ------------------------------------------------------------------ #
        parse_result = await dispatch_result.parser.parse(
            filename=filename,
            content_type=content_type,
            data=data,
        )

        # ------------------------------------------------------------------ #
        # 4. Placeholder chunking
        # ------------------------------------------------------------------ #
        chunks = await self._chunker.chunk(parsed=parse_result)
        return IngestionPipelineResult(
            validations=validations,
            dispatch=dispatch_result,
            parsed=parse_result,
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
