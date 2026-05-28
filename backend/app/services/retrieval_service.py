from __future__ import annotations

from app.models import QueryRequest, QueryResponse, QueryStatus


class RetrievalService:
    async def retrieve_answer(self, *, request: QueryRequest) -> QueryResponse:
        _ = request
        return QueryResponse(
            success=True,
            message="Retrieval placeholder (service scaffold).",
            answer="",
            status=QueryStatus.FAILED,
            confidence=0.0,
            retrieved_chunks=[],
            latency_ms=0.0,
        )
