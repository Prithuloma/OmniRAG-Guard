from __future__ import annotations

from app.services.retrieval_service import RetrievedChunk
from app.services.verification.lexical_scorer import compute_lexical_evidence_score
from app.services.verification.verification_models import VerificationResult

RETRIEVAL_CONFIDENCE_WEIGHT = 0.6
EVIDENCE_CONFIDENCE_WEIGHT = 0.4
DEFAULT_GROUNDED_THRESHOLD = 0.5

SUPPORTED_REASON = "Answer is supported by retrieved chunks."
INSUFFICIENT_OVERLAP_REASON = "Answer has insufficient lexical overlap with retrieved chunks."
NO_CHUNKS_REASON = "No retrieved chunks available for verification."
EMPTY_ANSWER_REASON = "Generated answer is empty and cannot be verified."


class VerificationService:
    def __init__(self, *, grounded_threshold: float = DEFAULT_GROUNDED_THRESHOLD) -> None:
        if not 0.0 <= grounded_threshold <= 1.0:
            raise ValueError("grounded_threshold must be between 0.0 and 1.0")
        self._grounded_threshold = grounded_threshold

    async def verify(
        self,
        *,
        query: str,
        generated_answer: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> VerificationResult:
        _ = query

        retrieval_confidence = _compute_retrieval_confidence(retrieved_chunks)
        normalized_answer = generated_answer.strip()

        if not normalized_answer:
            return VerificationResult(
                evidence_score=0.0,
                grounded=False,
                verification_reason=EMPTY_ANSWER_REASON,
                confidence=0.0,
                retrieval_confidence=retrieval_confidence,
                metadata={"strategy": "lexical_overlap"},
            )

        if not retrieved_chunks:
            return VerificationResult(
                evidence_score=0.0,
                grounded=False,
                verification_reason=NO_CHUNKS_REASON,
                confidence=_blend_confidence(
                    retrieval_confidence=retrieval_confidence,
                    evidence_score=0.0,
                ),
                retrieval_confidence=retrieval_confidence,
                metadata={"strategy": "lexical_overlap"},
            )

        chunk_texts = [chunk.text for chunk in retrieved_chunks]
        evidence_score = compute_lexical_evidence_score(normalized_answer, chunk_texts)
        grounded = evidence_score >= self._grounded_threshold
        verification_reason = (
            SUPPORTED_REASON if grounded else INSUFFICIENT_OVERLAP_REASON
        )
        confidence = _blend_confidence(
            retrieval_confidence=retrieval_confidence,
            evidence_score=evidence_score,
        )

        return VerificationResult(
            evidence_score=evidence_score,
            grounded=grounded,
            verification_reason=verification_reason,
            confidence=confidence,
            retrieval_confidence=retrieval_confidence,
            metadata={
                "strategy": "lexical_overlap",
                "grounded_threshold": self._grounded_threshold,
                "chunk_count": len(retrieved_chunks),
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
