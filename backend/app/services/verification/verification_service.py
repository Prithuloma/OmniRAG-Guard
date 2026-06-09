from __future__ import annotations

import logging
from typing import Any
from app.services.embeddings import EmbeddingService, BaseEmbedder
from app.services.retrieval_service import RetrievedChunk
from app.services.verification.lexical_scorer import compute_lexical_evidence_score
from app.services.verification.verification_models import VerificationResult

logger = logging.getLogger(__name__)

RETRIEVAL_CONFIDENCE_WEIGHT = 0.6
EVIDENCE_CONFIDENCE_WEIGHT = 0.4
DEFAULT_GROUNDED_THRESHOLD = 0.5

SUPPORTED_REASON = "Answer is supported by retrieved chunks."
INSUFFICIENT_OVERLAP_REASON = "Answer has insufficient lexical overlap with retrieved chunks."
NO_CHUNKS_REASON = "No retrieved chunks available for verification."
EMPTY_ANSWER_REASON = "Generated answer is empty and cannot be verified."


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class VerificationService:
    def __init__(
        self,
        *,
        grounded_threshold: float = DEFAULT_GROUNDED_THRESHOLD,
        embedder: BaseEmbedder | None = None,
    ) -> None:
        if not 0.0 <= grounded_threshold <= 1.0:
            raise ValueError("grounded_threshold must be between 0.0 and 1.0")
        self._grounded_threshold = grounded_threshold
        self._embedding_service = EmbeddingService(embedder=embedder)
        self._embedder = self._embedding_service._embedder

    async def verify(
        self,
        *,
        query: str,
        generated_answer: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> VerificationResult:
        logger.info(f"Verification requested: answer_length={len(generated_answer)}, chunks={len(retrieved_chunks)}")
        _ = query

        retrieval_confidence = _compute_retrieval_confidence(retrieved_chunks)
        normalized_answer = generated_answer.strip()

        if not normalized_answer:
            logger.warning("Empty answer provided to verification service.")
            return VerificationResult(
                evidence_score=0.0,
                grounded=False,
                verification_reason=EMPTY_ANSWER_REASON,
                confidence=0.0,
                grounding_score=0.0,
                citations=[],
                retrieval_confidence=retrieval_confidence,
                metadata={"strategy": "lexical_overlap"},
            )

        if not retrieved_chunks:
            logger.warning("No retrieved chunks provided to verification service.")
            return VerificationResult(
                evidence_score=0.0,
                grounded=False,
                verification_reason=NO_CHUNKS_REASON,
                confidence=_blend_confidence(
                    retrieval_confidence=retrieval_confidence,
                    evidence_score=0.0,
                ),
                grounding_score=0.0,
                citations=[],
                retrieval_confidence=retrieval_confidence,
                metadata={"strategy": "lexical_overlap"},
            )

        # 1. Lexical Scorer (evidence_score / lexical_score)
        chunk_texts = [chunk.text for chunk in retrieved_chunks]
        lexical_score = compute_lexical_evidence_score(normalized_answer, chunk_texts)

        # 2. Semantic Scorer
        try:
            answer_vec = (await self._embedder.embed([normalized_answer]))[0]
            chunk_vecs = await self._embedder.embed(chunk_texts)
            similarities = [cosine_similarity(answer_vec, cv) for cv in chunk_vecs]
            semantic_score = max(similarities) if similarities else 0.0
            chunk_consensus = sum(similarities) / len(similarities) if similarities else 0.0
        except Exception as exc:
            logger.warning(f"Semantic scoring failed, falling back to lexical scoring: {exc}")
            semantic_score = lexical_score
            similarities = [lexical_score] * len(retrieved_chunks)
            chunk_consensus = lexical_score

        # 3. Blended Grounding Score (Phase 6)
        grounding_score = 0.5 * lexical_score + 0.5 * semantic_score
        grounded = grounding_score >= self._grounded_threshold
        verification_reason = (
            SUPPORTED_REASON if grounded else INSUFFICIENT_OVERLAP_REASON
        )

        # 4. Confidence Calibration (Phase 9)
        confidence = 0.3 * retrieval_confidence + 0.5 * grounding_score + 0.2 * chunk_consensus
        confidence = max(0.0, min(1.0, confidence))

        # 5. Citations Extraction (Phase 7)
        citations = []
        for chunk, sim in zip(retrieved_chunks, similarities):
            words_chunk = set(chunk.text.lower().split())
            words_answer = set(normalized_answer.lower().split())
            intersection = words_chunk.intersection(words_answer)
            if sim >= 0.3 or len(intersection) >= 3 or (chunk.text.lower() in normalized_answer.lower()):
                citations.append({
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "page_number": chunk.page_number,
                })
        
        # Fallback: if no citations are found but chunks exist, cite the highest similarity chunk
        if not citations and retrieved_chunks:
            max_idx = similarities.index(max(similarities)) if similarities else 0
            chunk = retrieved_chunks[max_idx]
            citations.append({
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "page_number": chunk.page_number,
            })

        logger.info(f"Verification completed: grounded={grounded}, grounding_score={grounding_score:.4f}, confidence={confidence:.4f}, citations={len(citations)}")
        return VerificationResult(
            evidence_score=lexical_score,
            grounded=grounded,
            verification_reason=verification_reason,
            confidence=confidence,
            grounding_score=grounding_score,
            citations=citations,
            retrieval_confidence=retrieval_confidence,
            metadata={
                "strategy": "hybrid_lexical_semantic",
                "grounded_threshold": self._grounded_threshold,
                "chunk_count": len(retrieved_chunks),
                "lexical_score": lexical_score,
                "semantic_score": semantic_score,
                "chunk_consensus": chunk_consensus,
            },
        )


def _compute_retrieval_confidence(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0
    return sum(chunk.score for chunk in chunks) / len(chunks)


def _blend_confidence(*, retrieval_confidence: float, evidence_score: float) -> float:
    return (
        RETRIEVAL_CONFIDENCE_WEIGHT * retrieval_confidence
        + EVIDENCE_CONFIDENCE_WEIGHT * evidence_score
    )
