from __future__ import annotations

from typing import ClassVar
from sentence_transformers import SentenceTransformer

from app.services.embeddings.base_embedder import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    SentenceTransformerEmbedder wraps sentence-transformers library models,
    offering singleton loading and dimension auto-detection.
    """
    _model_cache: ClassVar[dict[str, SentenceTransformer]] = {}

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = self._get_or_load_model(model_name)
        # Dimension auto-detection
        self._dimension = self._model.get_sentence_embedding_dimension()

    @classmethod
    def _get_or_load_model(cls, model_name: str) -> SentenceTransformer:
        if model_name not in cls._model_cache:
            cls._model_cache[model_name] = SentenceTransformer(model_name)
        return cls._model_cache[model_name]

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Run encoding in a threadpool or synchronously, convert to python list
        embeddings = self._model.encode(texts)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(map(float, emb)) for emb in embeddings]
