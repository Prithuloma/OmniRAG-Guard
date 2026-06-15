from __future__ import annotations

from app.services.llm.base_llm import BaseLLM
from app.services.llm.llm_models import LLMContextChunk, LLMGenerationResult


def _compute_confidence(chunks: list[LLMContextChunk]) -> float:
    if not chunks:
        return 0.0
    return sum(chunk.score for chunk in chunks) / len(chunks)


def _extract_lead_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    for separator in (". ", "? ", "! ", "\n"):
        if separator in stripped:
            return stripped.split(separator, maxsplit=1)[0].strip()

    return stripped


class MockLLM(BaseLLM):
    """Deterministic LLM stub for development and tests."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        *,
        query: str,
        context: str,
        chunks: list[LLMContextChunk],
    ) -> LLMGenerationResult:
        _ = context

        if not chunks:
            return LLMGenerationResult(
                answer="The uploaded documents do not contain enough information to answer this question.",
                confidence=0.0,
                success=True,
                provider=self.provider_name,
                metadata={
                    "strategy": "no_context",
                    "title": "Empty Context Analysis",
                },
            )

        lead_sentence = _extract_lead_sentence(chunks[0].text)
        
        # Determine title from query words
        q_words = [w for w in query.strip().split() if len(w) > 3]
        title_words = q_words[:3] if q_words else ["Document", "Search"]
        title = " ".join(title_words).title()
        if not title:
            title = "Research Assistant Query"

        # Check if the query is a summarization request
        is_summary = False
        q_lower = query.lower().strip()
        summary_keywords = ["summarize", "summary", "overview", "explain this", "key points", "takeaway", "takeaways"]
        if any(k in q_lower for k in summary_keywords):
            is_summary = True

        if is_summary:
            title = "Document Summary"
            answer = (
                f"# Document Summary\n\n"
                f"## Overview\n"
                f"Based on the provided document context, this analysis provides a comprehensive overview of the contents. "
                f"The primary subject matter centers around the key principles highlighted in the retrieved text, "
                f"focusing on **{lead_sentence}** [1] as a fundamental starting point.\n\n"
                f"This document intelligence analysis synthesizes the key arguments, structured criteria, and "
                f"structural guidelines retrieved from the context to form a coherent overview of the source materials.\n\n"
                f"## Key Topics\n"
                f"- **Core Theme**: Focused on addressing the user prompt: *{query.strip()}*\n"
                f"- **Primary Domain**: Detailed analysis of the underlying systems and concepts mentioned in the text.\n"
                f"- **Evidence Baseline**: Grounded directly on the retrieved context chunks, referencing key source material [2].\n\n"
                f"## Important Takeaways\n"
                f"- **First Takeaway**: The document emphasizes the significance of **{lead_sentence}** as a foundational element.\n"
                f"- **Second Takeaway**: Careful evaluation of retrieved evidence shows consistent implementation patterns across the sections.\n"
                f"- **Third Takeaway**: Structuring document summaries helps streamline search, analysis, and discovery.\n\n"
                f"## Conclusion\n"
                f"In conclusion, the document provides a comprehensive treatment of the topic. By synthesizing these elements, "
                f"we can gain a solid understanding of the concepts outlined in the source materials."
            )
        elif lead_sentence:
            answer = (
                f"### Summary Overview\n"
                f"Based on the retrieved documents, **{lead_sentence}** [1]. This details the context of the user request.\n\n"
                f"### Key Details\n"
                f"- **Core Topic**: This addresses the question: *{query.strip()}*\n"
                f"- **Source Reference**: The context confirms this assertion."
            )
        else:
            answer = (
                f"### Retrieval Assessment\n"
                f"Based on the retrieved documents, the available context does not contain a clear answer to: *{query.strip()}*.\n\n"
                f"### Key Details\n"
                f"- **Inquiry**: {query.strip()}\n"
                f"- **Status**: Low matching evidence in database."
            )

        return LLMGenerationResult(
            answer=answer,
            confidence=_compute_confidence(chunks),
            success=True,
            provider=self.provider_name,
            metadata={
                "strategy": "template_summary" if not is_summary else "document_summary",
                "chunk_count": len(chunks),
                "title": title,
            },
        )
