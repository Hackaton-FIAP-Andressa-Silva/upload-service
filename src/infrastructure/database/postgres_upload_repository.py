from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.upload import Upload, UploadStatus
from src.domain.repositories.upload_repository import UploadRepository
from src.infrastructure.database.models import UploadModel


class PostgresUploadRepository(UploadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, upload: Upload) -> Upload:
        model = self._to_model(upload)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def find_by_id(self, upload_id: str) -> Optional[Upload]:
        result = await self._session.execute(
            select(UploadModel).where(UploadModel.id == upload_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def update(self, upload: Upload) -> Upload:
        result = await self._session.execute(
            select(UploadModel).where(UploadModel.id == upload.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Upload {upload.id} not found for update")

        model.status = upload.status.value
        model.error_message = upload.error_message
        model.updated_at = upload.updated_at

        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_model(upload: Upload) -> UploadModel:
        return UploadModel(
            id=upload.id,
            filename=upload.filename,
            content_type=upload.content_type,
            s3_key=upload.s3_key,
            file_size=upload.file_size,
            status=upload.status.value,
            error_message=upload.error_message,
            created_at=upload.created_at,
            updated_at=upload.updated_at,
        )

    @staticmethod
    def _to_entity(model: UploadModel) -> Upload:
        return Upload(
            id=model.id,
            filename=model.filename,
            content_type=model.content_type,
            s3_key=model.s3_key,
            file_size=model.file_size,
            status=UploadStatus(model.status),
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
