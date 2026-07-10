from __future__ import annotations

from app.services.llm.llm_models import LLMContextChunk


def assemble_context(chunks: list[LLMContextChunk]) -> str:
    """Build a deterministic prompt context block from retrieved chunks."""
    if not chunks:
        return ""

    sections: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        header = (
            f"[Source {index}] document_id={chunk.document_id} "
            f"page={chunk.page_number} score={chunk.score}"
        )
        sections.append(
            f"{header}\n"
            f"<source_text>\n"
            f"{chunk.text.strip()}\n"
            f"</source_text>"
        )

    return "\n\n".join(sections)
