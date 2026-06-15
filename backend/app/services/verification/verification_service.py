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
                claims=[],
                conflicts=[],
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
                claims=[],
                conflicts=[],
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
            chunk_vecs = []

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

        # 6. Claim-Level Grounding Visualizer & Highlights
        import re
        sentence_pattern = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s')
        raw_claims = [s.strip() for s in sentence_pattern.split(normalized_answer) if s.strip()]
        
        def clean_claim_text(text: str) -> str:
            t = re.sub(r'\*\*|\*', '', text)
            t = re.sub(r'^(?:[-\*\+]\s+|\d+\.\s+)', '', t.strip())
            return t.strip()

        claims_list = []
        for c_idx, raw_claim in enumerate(raw_claims):
            if raw_claim.startswith("#"):
                continue
            claim_text = clean_claim_text(raw_claim)
            if not claim_text:
                continue

            claim_lexical = compute_lexical_evidence_score(claim_text, chunk_texts)
            try:
                if chunk_vecs:
                    claim_vec = (await self._embedder.embed([claim_text]))[0]
                    claim_similarities = [cosine_similarity(claim_vec, cv) for cv in chunk_vecs]
                    max_claim_sim = max(claim_similarities) if claim_similarities else 0.0
                else:
                    max_claim_sim = claim_lexical
                    claim_similarities = [claim_lexical] * len(retrieved_chunks)
            except Exception as e:
                logger.warning(f"Failed to embed claim '{claim_text}': {e}")
                max_claim_sim = claim_lexical
                claim_similarities = [claim_lexical] * len(retrieved_chunks)

            claim_grounding = 0.5 * claim_lexical + 0.5 * max_claim_sim
            if claim_grounding >= 0.55:
                claim_status = "grounded"
            elif claim_grounding >= 0.35:
                claim_status = "partially_grounded"
            else:
                claim_status = "ungrounded"

            claim_citations = []
            for idx, (chunk, sim) in enumerate(zip(retrieved_chunks, claim_similarities)):
                words_chunk = set(chunk.text.lower().split())
                words_claim = set(claim_text.lower().split())
                intersection = words_chunk.intersection(words_claim)
                if sim >= 0.35 or len(intersection) >= 3 or (chunk.text.lower() in claim_text.lower()):
                    claim_citations.append({
                        "document_id": chunk.document_id,
                        "page_number": chunk.page_number,
                        "source_index": idx + 1,
                    })

            if not claim_citations and retrieved_chunks and max_claim_sim >= 0.2:
                max_sim_idx = claim_similarities.index(max(claim_similarities)) if claim_similarities else 0
                chunk = retrieved_chunks[max_sim_idx]
                claim_citations.append({
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "source_index": max_sim_idx + 1,
                })

            claims_list.append({
                "text": raw_claim,
                "grounding_score": claim_grounding,
                "status": claim_status,
                "citations": claim_citations,
            })

        # 7. Contradiction & Conflict Detector
        conflicts = []
        numbers_pattern = re.compile(r'\b\d+(?:\.\d+)?%?\b')
        negation_words = {"no", "not", "never", "declined", "failed", "opposite", "contradict", "decrease", "reduce"}

        for i in range(len(retrieved_chunks)):
            for j in range(i + 1, len(retrieved_chunks)):
                chunk_a = retrieved_chunks[i]
                chunk_b = retrieved_chunks[j]

                if chunk_a.document_id == chunk_b.document_id and chunk_a.page_number == chunk_b.page_number:
                    continue

                try:
                    sim = cosine_similarity(chunk_vecs[i], chunk_vecs[j]) if chunk_vecs else 0.0
                except Exception:
                    sim = 0.0

                if sim >= 0.5:
                    words_a = {w.lower() for w in chunk_a.text.split() if len(w) > 4}
                    words_b = {w.lower() for w in chunk_b.text.split() if len(w) > 4}
                    overlap_words = words_a.intersection(words_b)

                    if len(overlap_words) >= 2:
                        nums_a = set(numbers_pattern.findall(chunk_a.text))
                        nums_b = set(numbers_pattern.findall(chunk_b.text))

                        if nums_a and nums_b and nums_a != nums_b:
                            conflicts.append({
                                "source_a": chunk_a.document_id,
                                "source_b": chunk_b.document_id,
                                "page_a": chunk_a.page_number,
                                "page_b": chunk_b.page_number,
                                "description": f"Conflicting numeric data regarding {', '.join(list(overlap_words)[:2])}: "
                                               f"'{chunk_a.text[:60]}...' mentions {list(nums_a)} whereas "
                                               f"'{chunk_b.text[:60]}...' mentions {list(nums_b)}."
                            })
                        else:
                            has_neg_a = any(w in words_a for w in negation_words)
                            has_neg_b = any(w in words_b for w in negation_words)
                            if has_neg_a != has_neg_b:
                                conflicts.append({
                                    "source_a": chunk_a.document_id,
                                    "source_b": chunk_b.document_id,
                                    "page_a": chunk_a.page_number,
                                    "page_b": chunk_b.page_number,
                                    "description": f"Semantic polarity conflict regarding {', '.join(list(overlap_words)[:2])}: "
                                                   f"One source states: '{chunk_a.text[:55]}...' "
                                                   f"while the other states: '{chunk_b.text[:55]}...'."
                                })

        logger.info(f"Verification completed: grounded={grounded}, grounding_score={grounding_score:.4f}, confidence={confidence:.4f}, claims={len(claims_list)}, conflicts={len(conflicts)}")
        return VerificationResult(
            evidence_score=lexical_score,
            grounded=grounded,
            verification_reason=verification_reason,
            confidence=confidence,
            grounding_score=grounding_score,
            citations=citations,
            retrieval_confidence=retrieval_confidence,
            claims=claims_list,
            conflicts=conflicts,
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
