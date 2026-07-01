"""
tests/test_sentence_transformer_embedder.py
-------------------------------------------
Unit tests for the SentenceTransformerEmbedder class using mocks.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from app.services.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder


@patch("app.services.embeddings.sentence_transformer_embedder.SentenceTransformer")
def test_sentence_transformer_embedder_initialization(mock_sentence_transformer) -> None:
    # Set up mock behavior
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_sentence_transformer.return_value = mock_model

    # Clear cache to ensure constructor is fully executed
    SentenceTransformerEmbedder._model_cache.clear()

    embedder = SentenceTransformerEmbedder(model_name="mock-model")

    assert embedder.dimension == 384
    assert embedder.model_name == "mock-model"
    mock_sentence_transformer.assert_called_once_with("mock-model")
    mock_model.get_sentence_embedding_dimension.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.embeddings.sentence_transformer_embedder.SentenceTransformer")
async def test_sentence_transformer_embed_empty(mock_sentence_transformer) -> None:
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_sentence_transformer.return_value = mock_model

    SentenceTransformerEmbedder._model_cache.clear()
    embedder = SentenceTransformerEmbedder(model_name="mock-model")

    embeddings = await embedder.embed([])
    assert embeddings == []


@pytest.mark.asyncio
@patch("app.services.embeddings.sentence_transformer_embedder.SentenceTransformer")
async def test_sentence_transformer_embed_texts(mock_sentence_transformer) -> None:
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_model.encode.return_value = [[0.1] * 384, [0.2] * 384]
    mock_sentence_transformer.return_value = mock_model

    SentenceTransformerEmbedder._model_cache.clear()
    embedder = SentenceTransformerEmbedder(model_name="mock-model")

    texts = ["hello", "world"]
    embeddings = await embedder.embed(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1] * 384
    assert embeddings[1] == [0.2] * 384
    mock_model.encode.assert_called_once_with(texts)
