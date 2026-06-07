from fastapi import APIRouter, HTTPException, status

from app.models.request_models import QueryRequest
from app.models.response_models import (
    ErrorDetail,
    ErrorResponse,
    QueryResponse,
)
from app.services.query_service import QueryService, to_query_response

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

    Returns retrieved context chunks ranked by similarity to the query.

    Respects `top_k` and optional `filters.document_ids` / `filters.tags`.
    """
    service = QueryService()
    result = await service.execute_query(payload)

    if result.status == "empty_query":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": result.error.code.value if result.error else "EMPTY_QUERY",
                "message": result.error.message if result.error else "Query must not be empty.",
                "field": "query",
            },
        )

    if result.status in {"retrieval_failed", "qdrant_unavailable"}:
        error_code = result.error.code.value if result.error else "retrieval_failed"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorDetail(
                code=error_code.lower(),
                field="query",
                context={"detail": result.error.detail} if result.error and result.error.detail else None,
            ).model_dump(),
        )

    return to_query_response(result)
