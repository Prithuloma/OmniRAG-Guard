from fastapi import FastAPI

from app.routes.upload import router as upload_router

app = FastAPI(
    title="OmniRAG-Guard",
    version="0.1.0",
    description="Adaptive Multi-Modal RAG with Hallucination Verification and Cost-Aware Model Routing",
)

app.include_router(upload_router, prefix="/api/v1")
