from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Parse allowed origins
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
