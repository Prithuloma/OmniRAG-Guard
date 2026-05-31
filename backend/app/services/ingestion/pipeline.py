from __future__ import annotations

from dataclasses import dataclass

from app.services.chunking.chunk_models import ChunkingResult
from app.services.chunking.text_chunker import TextChunker
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
    chunking: ChunkingResult | None


class IngestionPipeline:
    def __init__(
        self,
        *,
        validator: FileValidator | None = None,
        parser: ParserDispatcher | None = None,
        chunker: TextChunker | None = None,
    ) -> None:
        self._validator = validator or FileValidator()
        self._parser = parser or ParserDispatcher()
        self._chunker = chunker or TextChunker()

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
                chunking=None,
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
                chunking=None,
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
        # 4. Chunk
        # ------------------------------------------------------------------ #
        chunking_result = self._chunker.chunk_text(
            text=parse_result.extracted_text,
            document_id=filename,
            metadata={
                "file_name": filename,
                "content_type": content_type,
                "parser_type": parse_result.parser_type.value,
                "parse_status": parse_result.status.value,
            },
        )
        return IngestionPipelineResult(
            validations=validations,
            dispatch=dispatch_result,
            parsed=parse_result,
            chunking=chunking_result,
        )

    async def run(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> IngestionPipelineResult:
        return await self.ingest(filename=filename, content_type=content_type, data=data)
