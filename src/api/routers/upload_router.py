import logging
import uuid as uuid_lib

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.upload_schema import UploadResponse, UploadStatusResponse, UpdateStatusRequest
from src.application.use_cases.create_upload_use_case import CreateUploadUseCase
from src.application.use_cases.get_upload_status_use_case import GetUploadStatusUseCase
from src.application.use_cases.update_upload_status_use_case import UpdateUploadStatusUseCase
from src.infrastructure.config import settings
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.postgres_upload_repository import PostgresUploadRepository
from src.infrastructure.messaging.sqs_publisher import SQSPublisher
from src.infrastructure.storage.s3_storage import S3Storage

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_valid_uuid(upload_id: str) -> str:
    """FastAPI dependency — raises 400 if *upload_id* is not a valid UUID v4."""
    try:
        val = uuid_lib.UUID(upload_id, version=4)
        if str(val) != upload_id:
            raise ValueError
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail={"error": "Invalid upload_id format", "code": "INVALID_UUID"})
    return upload_id


def get_create_use_case(session: AsyncSession = Depends(get_db_session)) -> CreateUploadUseCase:
    return CreateUploadUseCase(
        upload_repository=PostgresUploadRepository(session),
        storage_port=S3Storage(),
        messaging_port=SQSPublisher(),
    )


def get_status_use_case(session: AsyncSession = Depends(get_db_session)) -> GetUploadStatusUseCase:
    return GetUploadStatusUseCase(
        upload_repository=PostgresUploadRepository(session),
    )


def get_update_status_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> UpdateUploadStatusUseCase:
    return UpdateUploadStatusUseCase(
        upload_repository=PostgresUploadRepository(session),
    )


@router.post("/uploads", response_model=UploadResponse, status_code=202)
async def upload_diagram(
    file: UploadFile = File(...),
    use_case: CreateUploadUseCase = Depends(get_create_use_case),
):
    content = await file.read()
    result = await use_case.execute(
        filename=file.filename,
        content_type=file.content_type,
        file_content=content,
    )
    return UploadResponse(
        upload_id=result.upload_id,
        status=result.status,
        filename=result.filename,
        created_at=result.created_at,
    )


@router.get("/uploads/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str = Depends(_require_valid_uuid),
    use_case: GetUploadStatusUseCase = Depends(get_status_use_case),
):
    result = await use_case.execute(upload_id)
    return UploadStatusResponse(
        upload_id=result.upload_id,
        status=result.status,
        filename=result.filename,
        created_at=result.created_at,
        updated_at=result.updated_at,
        error_message=result.error_message,
    )


@router.patch("/uploads/{upload_id}/status", response_model=UploadStatusResponse)
async def update_upload_status(
    upload_id: str = Depends(_require_valid_uuid),
    body: UpdateStatusRequest = Body(...),
    x_internal_token: str = Header(..., alias="X-Internal-Token"),
    use_case: UpdateUploadStatusUseCase = Depends(get_update_status_use_case),
):
    """Internal endpoint — called only by ai-processing-service."""
    if x_internal_token != settings.INTERNAL_SERVICE_TOKEN:
        return JSONResponse(status_code=403, content={"error": "Forbidden", "code": "FORBIDDEN"})

    result = await use_case.execute(
        upload_id=upload_id,
        status=body.status,
        error_message=body.error_message,
    )
    return UploadStatusResponse(
        upload_id=result.upload_id,
        status=result.status,
        filename=result.filename,
        created_at=result.created_at,
        updated_at=result.updated_at,
        error_message=result.error_message,
    )
