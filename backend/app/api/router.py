from fastapi import APIRouter

from app.api.routes import health, upload, query

api_router = APIRouter()

# ── Core ──────────────────────────────────────────────────────────────────────
api_router.include_router(health.router, tags=["Health"])

# ── Documents ─────────────────────────────────────────────────────────────────
api_router.include_router(upload.router, prefix="/v1", tags=["Upload"])

# ── RAG ───────────────────────────────────────────────────────────────────────
api_router.include_router(query.router, prefix="/v1", tags=["Query"])
