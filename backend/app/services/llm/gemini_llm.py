from __future__ import annotations

import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.services.llm.base_llm import BaseLLM
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """Google Gemini LLM provider implementation."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model_name or settings.GEMINI_MODEL
        self._model_initialized = False
        
        # Configure the SDK if an API key is available
        if self._api_key:
            try:
                genai.configure(api_key=self._api_key)
                self._model_initialized = True
            except Exception as e:
                logger.error(f"Failed to configure Google Generative AI SDK: {e}")
        else:
            logger.warning("GeminiLLM initialized without an API key.")

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(
        self,
        *,
        query: str,
        context: str,
        chunks: list[LLMContextChunk],
    ) -> LLMGenerationResult:
        if not self._model_initialized:
            raise RuntimeError("Gemini model not initialized. Missing API key.")


        if not chunks:
            return LLMGenerationResult(
                answer="The uploaded documents do not contain enough information to answer this question.",
                confidence=0.0,
                success=True,
                provider=self.provider_name,
                metadata={"strategy": "no_context"},
            )

        system_instruction = (
            "You are a retrieval-augmented assistant.\n"
            "Answer the user's question ONLY using the provided retrieved context blocks wrapped in <source_text> tags.\n"
            "Do not hallucinate or answer from your own knowledge.\n"
            "If the answer cannot be found in the supplied context, explicitly state: "
            "\"The uploaded documents do not contain enough information to answer this question.\"\n"
            "Rely solely on the facts provided in the context. Do not mention or reference any facts not explicitly present in the context."
        )

        prompt = (
            f"Retrieved context:\n{context}\n\n"
            f"User Question: {query}\n\n"
            "Answer:"
        )

        generation_config = GenerationConfig(
            temperature=0.0,
        )

        try:
            model = genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_instruction
            )
            
            response = await model.generate_content_async(
                contents=prompt,
                generation_config=generation_config
            )
            
            answer = response.text.strip() if response.text else ""
            if not answer:
                answer = "The uploaded documents do not contain enough information to answer this question."

            confidence = sum(chunk.score for chunk in chunks) / len(chunks) if chunks else 0.0

            return LLMGenerationResult(
                answer=answer,
                confidence=confidence,
                success=True,
                provider=self.provider_name,
                metadata={
                    "model": self._model_name,
                    "chunk_count": len(chunks),
                },
            )
        except Exception as exc:
            logger.error(f"Gemini generation failed: {exc}")
            raise
