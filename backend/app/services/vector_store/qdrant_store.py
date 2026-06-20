from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid5, NAMESPACE_DNS

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.services.chunking.chunk_models import Chunk
from app.services.embeddings.embedding_models import Embedding
from app.services.embeddings.embedding_service import DEFAULT_EMBEDDING_DIMENSION

COLLECTION_NAME = "omnirag_documents"


class QdrantStoreError(Exception):
    """Base error for Qdrant vector store operations."""


class QdrantUnavailableError(QdrantStoreError):
    """Raised when Qdrant cannot be reached."""


class CollectionMissingError(QdrantStoreError):
    """Raised when the target collection does not exist."""


class EmptyVectorsError(QdrantStoreError):
    """Raised when no vectors are provided for upsert."""


class MalformedPayloadError(QdrantStoreError):
    """Raised when chunk/embedding inputs are invalid."""


@dataclass(frozen=True, slots=True)
class VectorSearchResult:
    chunk_text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class QdrantStore:
    def __init__(
        self,
        *,
        url: str | None = None,
        collection_name: str | None = None,
        vector_dimension: int | None = None,
        client: QdrantClient | None = None,
    ) -> None:
        from app.core.config import settings
        self._url = url or settings.QDRANT_URL
        self._collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self._vector_dimension = vector_dimension or settings.EMBEDDING_DIMENSION
        self._client = client

    @property
    def collection_name(self) -> str:
        return self._collection_name

    @property
    def vector_dimension(self) -> int:
        return self._vector_dimension

    def _get_client(self) -> QdrantClient:
        if self._client is not None:
            return self._client

        try:
            # 1. Try remote connection with small timeout check
            client = QdrantClient(url=self._url, timeout=1.0)
            client.get_collections()
            self._client = client
            return self._client
        except Exception as exc1:
            # 2. Fall back to local file-based embedded Qdrant instance
            import logging
            logging.getLogger(__name__).warning(
                f"Qdrant daemon at {self._url} not running. Falling back to local embedded vector store at storage/qdrant_db"
            )
            try:
                self._client = QdrantClient(path="storage/qdrant_db")
                return self._client
            except Exception as exc2:
                raise QdrantUnavailableError(
                    f"Qdrant remote and local embedded engines are both unavailable: {exc1} / {exc2}"
                ) from exc2

    def initialize_collection(self) -> None:
        try:
            client = self._get_client()
            if client.collection_exists(self._collection_name):
                return

            client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=self._vector_dimension,
                    distance=models.Distance.COSINE,
                ),
            )
        except QdrantStoreError:
            raise
        except Exception as exc:
            raise QdrantUnavailableError(
                f"Failed to initialize collection '{self._collection_name}'"
            ) from exc

    def _ensure_collection_exists(self) -> None:
        try:
            client = self._get_client()
            if not client.collection_exists(self._collection_name):
                raise CollectionMissingError(
                    f"Collection '{self._collection_name}' does not exist"
                )
        except CollectionMissingError:
            raise
        except Exception as exc:
            raise QdrantUnavailableError(
                f"Unable to verify collection '{self._collection_name}'"
            ) from exc


    def upsert_chunks(
        self,
        *,
        chunks: list[Chunk],
        embeddings: list[Embedding],
    ) -> int:
        if not chunks or not embeddings:
            raise EmptyVectorsError("chunks and embeddings must be non-empty")

        if len(chunks) != len(embeddings):
            raise MalformedPayloadError(
                "chunks and embeddings must contain the same number of items"
            )

        points: list[models.PointStruct] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            if chunk.chunk_id != embedding.chunk_id:
                raise MalformedPayloadError(
                    f"chunk_id mismatch: {chunk.chunk_id} != {embedding.chunk_id}"
                )

            if not embedding.vector:
                raise EmptyVectorsError(
                    f"embedding vector is empty for chunk '{chunk.chunk_id}'"
                )

            if len(embedding.vector) != self._vector_dimension:
                raise MalformedPayloadError(
                    f"vector dimension mismatch for chunk '{chunk.chunk_id}': "
                    f"expected {self._vector_dimension}, got {len(embedding.vector)}"
                )

            points.append(
                models.PointStruct(
                    id=self._point_id(chunk.chunk_id),
                    vector=embedding.vector,
                    payload=self._build_payload(chunk),
                )
            )

        self.initialize_collection()
        client = self._get_client()

        try:
            client.upsert(collection_name=self._collection_name, points=points)
        except UnexpectedResponse as exc:
            raise QdrantUnavailableError(
                f"Failed to upsert vectors into '{self._collection_name}'"
            ) from exc
        except Exception as exc:
            raise QdrantUnavailableError(
                f"Failed to upsert vectors into '{self._collection_name}'"
            ) from exc

        return len(points)

    def search(
        self,
        *,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Any | None = None,
    ) -> list[VectorSearchResult]:
        if not query_embedding:
            raise EmptyVectorsError("query_embedding must be non-empty")

        if len(query_embedding) != self._vector_dimension:
            raise MalformedPayloadError(
                f"query vector dimension mismatch: expected {self._vector_dimension}, "
                f"got {len(query_embedding)}"
            )

        if top_k <= 0:
            raise MalformedPayloadError("top_k must be positive")

        self._ensure_collection_exists()
        client = self._get_client()

        qdrant_filter = None
        if filters:
            must_conditions = []
            document_ids = getattr(filters, "document_ids", None) or (filters.get("document_ids") if isinstance(filters, dict) else None)
            document_id = getattr(filters, "document_id", None) or (filters.get("document_id") if isinstance(filters, dict) else None)
            tags = getattr(filters, "tags", None) or (filters.get("tags") if isinstance(filters, dict) else None)
            filename = getattr(filters, "filename", None) or (filters.get("filename") if isinstance(filters, dict) else None)
            upload_date = getattr(filters, "upload_date", None) or (filters.get("upload_date") if isinstance(filters, dict) else None)

            if document_id:
                if not document_ids:
                    document_ids = [document_id]
                elif document_id not in document_ids:
                    document_ids = list(document_ids) + [document_id]

            if document_ids:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchAny(any=document_ids),
                    )
                )

            if tags:
                for tag in tags:
                    must_conditions.append(
                        models.FieldCondition(
                            key="tags",
                            match=models.MatchValue(value=tag),
                        )
                    )

            if filename:
                must_conditions.append(
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchValue(value=filename),
                    )
                )

            if upload_date:
                must_conditions.append(
                    models.FieldCondition(
                        key="upload_date",
                        match=models.MatchValue(value=upload_date),
                    )
                )

            if must_conditions:
                qdrant_filter = models.Filter(must=must_conditions)

        try:
            response = client.query_points(
                collection_name=self._collection_name,
                query=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
        except UnexpectedResponse as exc:
            raise QdrantUnavailableError(
                f"Search failed for collection '{self._collection_name}'"
            ) from exc
        except Exception as exc:
            raise QdrantUnavailableError(
                f"Search failed for collection '{self._collection_name}'"
            ) from exc

        results: list[VectorSearchResult] = []
        for hit in response.points:
            payload = hit.payload or {}
            chunk_text = payload.get("chunk_text")
            if not isinstance(chunk_text, str):
                raise MalformedPayloadError(
                    f"search hit missing valid chunk_text payload for point '{hit.id}'"
                )

            metadata = {
                "document_id": payload.get("document_id"),
                "chunk_id": payload.get("chunk_id"),
                "page_number": payload.get("page_number"),
                "source_file": payload.get("source_file"),
            }
            results.append(
                VectorSearchResult(
                    chunk_text=chunk_text,
                    score=float(hit.score),
                    metadata=metadata,
                )
            )

        return results

    def delete_document(self, *, document_id: str) -> int:
        if not document_id:
            raise MalformedPayloadError("document_id must be non-empty")

        self._ensure_collection_exists()
        client = self._get_client()

        try:
            existing = client.scroll(
                collection_name=self._collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                ),
                limit=10_000,
                with_payload=False,
            )
            point_ids = [point.id for point in existing[0]]
            if not point_ids:
                return 0

            client.delete(
                collection_name=self._collection_name,
                points_selector=models.PointIdsList(points=point_ids),
            )
            return len(point_ids)
        except UnexpectedResponse as exc:
            raise QdrantUnavailableError(
                f"Failed to delete document '{document_id}'"
            ) from exc
        except QdrantStoreError:
            raise
        except Exception as exc:
            raise QdrantUnavailableError(
                f"Failed to delete document '{document_id}'"
            ) from exc

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        return str(uuid5(NAMESPACE_DNS, chunk_id))

    @staticmethod
    def _build_payload(chunk: Chunk) -> dict[str, Any]:
        page_number = chunk.metadata.get("page_number")
        source_file = chunk.metadata.get("file_name", chunk.document_id)

        payload = {
            "document_id": chunk.document_id,
            "chunk_id": chunk.chunk_id,
            "page_number": page_number,
            "source_file": source_file,
            "chunk_text": chunk.content,
            "filename": chunk.metadata.get("file_name") or chunk.metadata.get("filename") or source_file,
            "tags": chunk.metadata.get("tags") or [],
            "upload_date": chunk.metadata.get("upload_date"),
        }
        for k, v in chunk.metadata.items():
            if k not in payload and v is not None:
                payload[k] = v
        return payload
