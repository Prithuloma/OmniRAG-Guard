from fastapi import APIRouter, File, Form, UploadFile, status

from app.models.request_models import UploadMetadata, UploadRequest
from app.models.response_models import ErrorResponse, UploadResponse
from app.services import IngestionService

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document for ingestion",
    responses={
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
    tags=["Upload"],
)
async def upload_document(
    file: UploadFile = File(..., description="PDF, TXT, or DOCX file to ingest."),
    title: str | None = Form(default=None, description="Optional document title."),
    tags: str = Form(default="", description="Comma-separated tags, e.g. 'finance,q3'."),
) -> UploadResponse:
    """
    Accept a document upload and enqueue it for the ingestion pipeline.

    Returns a stable `document_id` and an initial `status` of **pending**.
    Poll `GET /documents/{document_id}` (future) to track pipeline progress.

    > ⚠️ Ingestion logic is not yet implemented — mock response returned.
    """
    contents = await file.read()
    service = IngestionService()

    request = UploadRequest(
        metadata=UploadMetadata(
            title=title,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
    )
    return await service.ingest_document(
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        data=contents,
        request=request,
    )
