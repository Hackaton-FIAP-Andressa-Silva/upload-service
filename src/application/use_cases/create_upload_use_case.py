import logging
import uuid
from typing import Set

from src.application.dtos.upload_dto import UploadDTO
from src.application.ports.messaging_port import MessagingPort
from src.application.ports.storage_port import StoragePort
from src.application.use_cases.file_validator import (
    MagicBytesMismatchError,
    validate_magic_bytes,
)
from src.domain.entities.upload import Upload
from src.domain.repositories.upload_repository import UploadRepository

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES: Set[str] = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/pdf",
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class InvalidFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class StorageError(Exception):
    pass


class CreateUploadUseCase:
    def __init__(
        self,
        upload_repository: UploadRepository,
        storage_port: StoragePort,
        messaging_port: MessagingPort,
    ) -> None:
        self._repository = upload_repository
        self._storage = storage_port
        self._messaging = messaging_port

    async def execute(
        self,
        filename: str,
        content_type: str,
        file_content: bytes,
    ) -> UploadDTO:
        file_size = len(file_content)

        # Validate content type (MIME allowlist)
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidFileTypeError(
                f"File type '{content_type}' is not allowed. "
                f"Accepted types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            )

        # Validate file size — reject before any storage operation
        if file_size > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(
                f"File size {file_size} bytes exceeds maximum of {MAX_FILE_SIZE_BYTES} bytes (20 MB)"
            )

        # Validate magic bytes — prevents MIME-type spoofing
        try:
            validate_magic_bytes(file_content, content_type)
        except MagicBytesMismatchError as exc:
            raise InvalidFileTypeError(str(exc)) from exc

        # Build S3 key
        upload_id = str(uuid.uuid4())
        s3_key = f"uploads/{upload_id}/{filename}"

        # Upload to S3
        try:
            await self._storage.upload(s3_key, file_content, content_type)
        except Exception as exc:
            logger.error(
                "Failed to upload file to storage",
                extra={"upload_id": upload_id, "error": str(exc)},
            )
            raise StorageError(f"Failed to store file: {exc}") from exc

        # Persist metadata
        upload = Upload.create(
            filename=filename,
            content_type=content_type,
            s3_key=s3_key,
            file_size=file_size,
        )
        # Override with deterministic ID so S3 key and DB match
        upload.id = upload_id
        await self._repository.save(upload)

        # Publish async job
        await self._messaging.publish(
            upload_id=upload.id,
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
        )

        logger.info(
            "Upload created successfully",
            extra={"upload_id": upload.id, "upload_filename": filename, "file_size": file_size},
        )

        return UploadDTO(
            upload_id=upload.id,
            status=upload.status.value,
            filename=upload.filename,
            created_at=upload.created_at,
        )
