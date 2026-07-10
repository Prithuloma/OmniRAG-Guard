from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────
    APP_TITLE: str = "OmniRAG-Guard"
    APP_VERSION: str = "0.1.0"

    # ── Server ────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Environment ───────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"

    # ── Qdrant ────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "omnirag_documents"
    QDRANT_API_KEY: str | None = None

    # ── Gemini / LLM ──────────────────────────────────────
    GEMINI_API_KEY: str | None = None
    LLM_PROVIDER: str = "mock"
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── Embeddings ────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ── Storage ───────────────────────────────────────────
    UPLOAD_DIR: str = "storage/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
