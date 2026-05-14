import logging
import uuid
from datetime import datetime, timezone

import aioboto3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.application.use_cases.create_upload_use_case import (
    FileTooLargeError,
    InvalidFileTypeError,
    StorageError,
)
from src.application.use_cases.get_upload_status_use_case import UploadNotFoundError
from src.infrastructure.config import settings
from src.infrastructure.database.connection import AsyncSessionFactory
from src.infrastructure.logging_config import setup_logging, trace_id_var

setup_logging(settings.APP_NAME)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Upload Service",
    description="Receives architecture diagrams and triggers AI analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    token = trace_id_var.set(trace_id)
    try:
        response = await call_next(request)
    finally:
        trace_id_var.reset(token)
    response.headers["X-Trace-ID"] = trace_id
    return response


@app.exception_handler(InvalidFileTypeError)
async def invalid_file_type_handler(request: Request, exc: InvalidFileTypeError):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "code": "INVALID_FILE_TYPE", "trace_id": trace_id},
    )


@app.exception_handler(FileTooLargeError)
async def file_too_large_handler(request: Request, exc: FileTooLargeError):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=413,
        content={"error": str(exc), "code": "FILE_TOO_LARGE", "trace_id": trace_id},
    )


@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, exc: StorageError):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=503,
        content={"error": "Storage service unavailable", "code": "STORAGE_ERROR", "trace_id": trace_id},
    )


@app.exception_handler(UploadNotFoundError)
async def upload_not_found_handler(request: Request, exc: UploadNotFoundError):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=404,
        content={"error": str(exc), "code": "UPLOAD_NOT_FOUND", "trace_id": trace_id},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.error("Unhandled exception: %s | path=%s", str(exc), request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR", "trace_id": trace_id},
    )


def _boto_kwargs() -> dict:
    kwargs: dict = {"region_name": settings.AWS_REGION}
    if settings.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return kwargs


@app.get("/health")
async def health_check():
    checks: dict = {}
    overall = "healthy"

    # --- PostgreSQL ---
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as exc:
        logger.error("Health check: database unreachable: %s", exc)
        checks["database"] = {"status": "unhealthy", "error": "Connection failed"}
        overall = "unhealthy"

    # --- S3 ---
    try:
        boto_session = aioboto3.Session()
        async with boto_session.client("s3", **_boto_kwargs()) as s3:
            await s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        checks["s3"] = {"status": "healthy"}
    except Exception as exc:
        logger.warning("Health check: S3 degraded: %s", exc)
        checks["s3"] = {"status": "degraded"}
        if overall == "healthy":
            overall = "degraded"

    # --- SQS ---
    try:
        boto_session = aioboto3.Session()
        async with boto_session.client("sqs", **_boto_kwargs()) as sqs:
            await sqs.get_queue_attributes(
                QueueUrl=settings.SQS_QUEUE_URL,
                AttributeNames=["ApproximateNumberOfMessages"],
            )
        checks["sqs"] = {"status": "healthy"}
    except Exception as exc:
        logger.warning("Health check: SQS degraded: %s", exc)
        checks["sqs"] = {"status": "degraded"}
        if overall == "healthy":
            overall = "degraded"

    status_code = 503 if overall == "unhealthy" else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "service": settings.APP_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        },
    )


# Import and include routers after app setup
from src.api.routers.upload_router import router as upload_router  # noqa: E402
app.include_router(upload_router, prefix="/api/v1")
