from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=not settings.is_production,
)

app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "app": settings.APP_TITLE,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "status": "running",
        }
    )
