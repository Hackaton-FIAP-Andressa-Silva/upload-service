import logging

from src.application.dtos.upload_dto import UploadStatusDTO
from src.domain.repositories.upload_repository import UploadRepository

logger = logging.getLogger(__name__)


class UploadNotFoundError(Exception):
    pass


class GetUploadStatusUseCase:
    def __init__(self, upload_repository: UploadRepository) -> None:
        self._repository = upload_repository

    async def execute(self, upload_id: str) -> UploadStatusDTO:
        upload = await self._repository.find_by_id(upload_id)

        if upload is None:
            raise UploadNotFoundError(f"Upload '{upload_id}' not found")

        logger.info(
            "Upload status retrieved",
            extra={"upload_id": upload_id, "status": upload.status.value},
        )

        return UploadStatusDTO(
            upload_id=upload.id,
            status=upload.status.value,
            filename=upload.filename,
            created_at=upload.created_at,
            updated_at=upload.updated_at,
            error_message=upload.error_message,
        )
