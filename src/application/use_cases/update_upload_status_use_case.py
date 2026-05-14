import logging

from src.application.dtos.upload_dto import UploadStatusDTO
from src.domain.entities.upload import UploadStatus
from src.domain.repositories.upload_repository import UploadRepository

logger = logging.getLogger(__name__)


class UploadNotFoundError(Exception):
    pass


class UpdateUploadStatusUseCase:
    """Internal use case called by AI Processing Service via REST."""

    def __init__(self, upload_repository: UploadRepository) -> None:
        self._repository = upload_repository

    async def execute(
        self,
        upload_id: str,
        status: str,
        error_message: str | None = None,
    ) -> UploadStatusDTO:
        upload = await self._repository.find_by_id(upload_id)

        if upload is None:
            raise UploadNotFoundError(f"Upload '{upload_id}' not found")

        upload.update_status(UploadStatus(status), error_message)
        await self._repository.update(upload)

        logger.info(
            "Upload status updated",
            extra={"upload_id": upload_id, "new_status": status},
        )

        return UploadStatusDTO(
            upload_id=upload.id,
            status=upload.status.value,
            filename=upload.filename,
            created_at=upload.created_at,
            updated_at=upload.updated_at,
            error_message=upload.error_message,
        )
