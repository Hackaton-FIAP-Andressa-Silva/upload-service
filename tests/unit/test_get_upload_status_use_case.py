import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.application.use_cases.get_upload_status_use_case import (
    GetUploadStatusUseCase,
    UploadNotFoundError,
)
from src.domain.entities.upload import Upload, UploadStatus


@pytest.fixture
def sample_upload():
    return Upload(
        id="test-uuid-123",
        filename="arch.png",
        content_type="image/png",
        s3_key="uploads/test-uuid-123/arch.png",
        file_size=1024,
        status=UploadStatus.ANALYZED,
        created_at=datetime(2026, 5, 8, 10, 0, 0),
        updated_at=datetime(2026, 5, 8, 10, 1, 0),
        error_message=None,
    )


@pytest.mark.asyncio
async def test_get_status_existing_upload(sample_upload):
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=sample_upload)
    use_case = GetUploadStatusUseCase(repo)

    result = await use_case.execute("test-uuid-123")

    assert result.upload_id == "test-uuid-123"
    assert result.status == "ANALYZED"
    assert result.filename == "arch.png"
    assert result.error_message is None


@pytest.mark.asyncio
async def test_get_status_not_found():
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    use_case = GetUploadStatusUseCase(repo)

    with pytest.raises(UploadNotFoundError):
        await use_case.execute("non-existent-id")
