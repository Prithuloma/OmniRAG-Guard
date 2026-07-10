from __future__ import annotations

import hashlib
import struct
from typing import Any

from app.core.config import settings
from app.services.chunking.chunk_models import Chunk
from app.services.embeddings.base_embedder import BaseEmbedder
from app.services.embeddings.embedding_models import Embedding, EmbeddingResult
from app.services.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder

DEFAULT_EMBEDDING_DIMENSION = 384


def deterministic_vector(text: str, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> list[float]:
    """Generate a deterministic pseudo-random vector from text content."""
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0

    while len(values) < dimension:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for index in range(0, len(block) - 3, 4):
            unsigned = struct.unpack("!I", block[index : index + 4])[0]
            values.append((unsigned / 2**32) * 2 - 1)
            if len(values) >= dimension:
                break
        counter += 1

    return values[:dimension]


class PlaceholderEmbedder(BaseEmbedder):
    def __init__(self, *, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [deterministic_vector(text, self._dimension) for text in texts]


class EmbeddingService:
    def __init__(self, *, embedder: BaseEmbedder | None = None) -> None:
        if embedder is not None:
            self._embedder = embedder
        elif settings.EMBEDDING_PROVIDER == "sentence-transformers":
            self._embedder = SentenceTransformerEmbedder(model_name=settings.EMBEDDING_MODEL)
        else:
            self._embedder = PlaceholderEmbedder(dimension=settings.EMBEDDING_DIMENSION)

    @property
    def dimension(self) -> int:
        return self._embedder.dimension

    async def embed_chunks(self, chunks: list[Chunk]) -> EmbeddingResult:
        if not chunks:
            return EmbeddingResult(success=True, total_embeddings=0, embeddings=[])

        vectors = await self._embedder.embed([chunk.content for chunk in chunks])
        embeddings = [
            self._build_embedding(chunk=chunk, vector=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        return EmbeddingResult(
            success=True,
            total_embeddings=len(embeddings),
            embeddings=embeddings,
        )

    def _build_embedding(self, *, chunk: Chunk, vector: list[float]) -> Embedding:
        metadata: dict[str, Any] = {
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
        }
        return Embedding(
            embedding_id=f"{chunk.chunk_id}:embedding",
            chunk_id=chunk.chunk_id,
            vector=vector,
            dimension=len(vector),
            metadata=metadata,
        )
