from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from app.core.config import settings
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.chunking.chunk_models import Chunk
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    health_status = {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "qdrant": "unknown",
            "embeddings": "unknown"
        }
    }
    
    # 1. Verify Qdrant connection
    try:
        client = QdrantClient(url=settings.QDRANT_URL, timeout=2.0)
        client.get_collections()
        health_status["services"]["qdrant"] = "healthy"
    except Exception as exc:
        logger.error(f"Health check failed for Qdrant: {exc}")
        health_status["services"]["qdrant"] = f"unhealthy: {exc}"
        health_status["status"] = "unhealthy"

    # 2. Verify Embedding model availability
    try:
        service = EmbeddingService()
        test_chunk = Chunk(
            chunk_id="health_test",
            document_id="health_test",
            content="health check",
            chunk_index=0,
            start_char=0,
            end_char=12,
            metadata={}
        )
        res = await service.embed_chunks([test_chunk])
        if res.success and res.total_embeddings > 0:
            health_status["services"]["embeddings"] = "healthy"
        else:
            health_status["services"]["embeddings"] = "unhealthy: no embeddings generated"
            health_status["status"] = "unhealthy"
    except Exception as exc:
        logger.error(f"Health check failed for embeddings: {exc}")
        health_status["services"]["embeddings"] = f"unhealthy: {exc}"
        health_status["status"] = "unhealthy"

    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=status_code, content=health_status)
