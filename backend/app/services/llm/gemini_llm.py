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

        is_summary = False
        q_lower = query.lower().strip()
        summary_keywords = ["summarize", "summary", "overview", "explain this", "key points", "takeaway", "takeaways"]
        if any(k in q_lower for k in summary_keywords):
            is_summary = True

        if is_summary:
            system_instruction = (
                "You are a document intelligence assistant. Your task is to summarize the entire provided context.\n"
                "Answer ONLY using the provided retrieved context blocks wrapped in <source_text> tags.\n\n"
                "Formatting Rules:\n"
                "1. ALWAYS begin your response with a 2-4 word conversation title wrapped in <title>Title Here</title>, e.g., <title>BFS vs DFS</title>.\n"
                "2. Format the response exactly as follows:\n\n"
                "# Document Summary\n\n"
                "## Overview\n"
                "[A concise 2-4 paragraph overview of the entire document context]\n\n"
                "## Key Topics\n"
                "[Bullet points of the major concepts covered in the document]\n\n"
                "## Important Takeaways\n"
                "[Bullet points of concise actionable or memorable takeaways from the document]\n\n"
                "## Conclusion\n"
                "[A short concluding paragraph that ties everything together]\n\n"
                "3. Include precise inline citation markers like [1], [2], etc., immediately after statements. Do not create a separate 'Sources' section yourself.\n"
                "4. NEVER output any meta-commentary, correction acknowledgments, or references to refinement feedback (such as 'Here is the revised response', or '[REFINEMENT FEEDBACK]'). Write only the clean, final document summary directly.\n"
                "5. Image Generation: If the user explicitly asks for an image, diagram, chart, visual illustration, or conceptual representation of something described in the context, you can generate it using Pollinations AI by embedding a markdown image with a descriptive, URL-encoded prompt in this format: `![Description](https://image.pollinations.ai/prompt/encoded_prompt?width=1024&height=1024&nologo=true)`. Ensure the prompt is detailed and properly URL-encoded. You must still base the visualization strictly on the provided context facts."
            )
        else:
            system_instruction = (
                "You are a retrieval-augmented assistant.\n"
                "Answer the user's question ONLY using the provided retrieved context blocks wrapped in <source_text> tags.\n"
                "Do not hallucinate or answer from your own knowledge.\n"
                "If the answer cannot be found in the supplied context, explicitly state: "
                "\"The uploaded documents do not contain enough information to answer this question.\"\n"
                "Rely solely on the facts provided in the context. Do not mention or reference any facts not explicitly present in the context.\n\n"
                "Formatting Rules:\n"
                "1. ALWAYS begin your response with a 2-4 word conversation title wrapped in <title>Title Here</title>, e.g., <title>BFS vs DFS</title>.\n"
                "2. Format the response beautifully using Markdown with logical headings (e.g. ### Key Concepts, ### Analysis, etc.), short paragraphs, and bullet points.\n"
                "3. Include precise inline citation markers like [1], [2], etc., immediately after any statement referencing context block '[Source 1]', '[Source 2]', etc.\n"
                "4. NEVER output any meta-commentary, correction acknowledgments, or references to refinement feedback (such as 'Here is the revised response', or '[REFINEMENT FEEDBACK]'). Write only the clean, final response directly.\n"
                "5. Image Generation: If the user explicitly asks for an image, diagram, chart, visual illustration, or conceptual representation of something described in the context, you can generate it using Pollinations AI by embedding a markdown image with a descriptive, URL-encoded prompt in this format: `![Description](https://image.pollinations.ai/prompt/encoded_prompt?width=1024&height=1024&nologo=true)`. Ensure the prompt is detailed and properly URL-encoded. You must still base the visualization strictly on the provided context facts."
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
            
            raw_answer = response.text.strip() if response.text else ""
            import re
            title = "Untitled Chat"
            answer = raw_answer
            
            title_match = re.search(r"<title>(.*?)</title>", raw_answer, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                answer = re.sub(r"<title>.*?</title>", "", raw_answer, flags=re.DOTALL).strip()
                
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
                    "title": title,
                },
            )
        except Exception as exc:
            logger.error(f"Gemini generation failed: {exc}")
            raise
