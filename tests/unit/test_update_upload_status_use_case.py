import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.application.use_cases.update_upload_status_use_case import (
    UpdateUploadStatusUseCase,
    UploadNotFoundError,
)
from src.domain.entities.upload import Upload, UploadStatus


@pytest.fixture
def sample_upload():
    return Upload(
        id="upload-id-1",
        filename="arch.png",
        content_type="image/png",
        s3_key="uploads/upload-id-1/arch.png",
        file_size=1024,
        status=UploadStatus.PROCESSING,
        created_at=datetime(2026, 5, 14, 10, 0, 0),
        updated_at=datetime(2026, 5, 14, 10, 0, 1),
    )


@pytest.mark.asyncio
async def test_update_to_analyzed(sample_upload):
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=sample_upload)
    repo.update = AsyncMock(return_value=None)
    use_case = UpdateUploadStatusUseCase(repo)

    result = await use_case.execute("upload-id-1", "ANALYZED")

    assert result.upload_id == "upload-id-1"
    assert result.status == "ANALYZED"
    assert result.filename == "arch.png"
    repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_to_error_with_message(sample_upload):
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=sample_upload)
    repo.update = AsyncMock(return_value=None)
    use_case = UpdateUploadStatusUseCase(repo)

    result = await use_case.execute("upload-id-1", "ERROR", error_message="AI failed")

    assert result.status == "ERROR"
    assert result.error_message == "AI failed"
    repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_not_found_raises():
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    use_case = UpdateUploadStatusUseCase(repo)

    with pytest.raises(UploadNotFoundError):
        await use_case.execute("non-existent", "ANALYZED")


@pytest.mark.asyncio
async def test_update_to_processing(sample_upload):
    sample_upload.status = UploadStatus.RECEIVED
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=sample_upload)
    repo.update = AsyncMock(return_value=None)
    use_case = UpdateUploadStatusUseCase(repo)

    result = await use_case.execute("upload-id-1", "PROCESSING")

    assert result.status == "PROCESSING"


@pytest.mark.asyncio
async def test_update_returns_updated_at(sample_upload):
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=sample_upload)
    repo.update = AsyncMock(return_value=None)
    use_case = UpdateUploadStatusUseCase(repo)

    result = await use_case.execute("upload-id-1", "ANALYZED")

    assert result.updated_at is not None
