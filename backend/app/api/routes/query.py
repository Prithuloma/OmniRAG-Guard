from fastapi import APIRouter, status

from app.models.request_models import QueryRequest
from app.models.response_models import (
    ErrorResponse,
    QueryResponse,
)
from app.services import RetrievalService

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a query to the RAG pipeline",
    responses={
        422: {"description": "Validation error — check request body"},
        503: {"model": ErrorResponse, "description": "RAG pipeline unavailable"},
    },
    tags=["Query"],
)
async def query_documents(payload: QueryRequest) -> QueryResponse:
    """
    Submit a natural-language query against ingested documents.

    Returns a synthesised **answer**, a **confidence** score, and the
    **retrieved chunks** that grounded the answer.

    Respects `top_k` and optional `filters.document_ids` / `filters.tags`.

    > ⚠️ Retrieval and generation logic is not yet implemented — mock response returned.
    """
    service = RetrievalService()
    return await service.retrieve_answer(request=payload)
