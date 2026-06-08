from __future__ import annotations

import re

_TOKEN_PATTERN = re.compile(r"\b\w+\b")
_MIN_TOKEN_LENGTH = 2


def tokenize(text: str) -> set[str]:
    """Extract normalized lexical tokens from text."""
    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) >= _MIN_TOKEN_LENGTH
    }


def compute_lexical_evidence_score(answer: str, chunk_texts: list[str]) -> float:
    """
    Compute evidence score from lexical overlap between the answer and each chunk.

    For each chunk, uses the stronger of:
      - answer coverage: matched tokens / answer tokens
      - chunk coverage: matched tokens / chunk tokens

    The final score is the maximum per-chunk overlap, clamped to [0.0, 1.0].
    """
    answer_tokens = tokenize(answer)
    if not answer_tokens or not chunk_texts:
        return 0.0

    chunk_scores: list[float] = []
    for chunk_text in chunk_texts:
        chunk_tokens = tokenize(chunk_text)
        if not chunk_tokens:
            continue

        matched_tokens = answer_tokens & chunk_tokens
        if not matched_tokens:
            chunk_scores.append(0.0)
            continue

        answer_coverage = len(matched_tokens) / len(answer_tokens)
        chunk_coverage = len(matched_tokens) / len(chunk_tokens)
        chunk_scores.append(max(answer_coverage, chunk_coverage))

    if not chunk_scores:
        return 0.0

    return min(1.0, max(0.0, max(chunk_scores)))
