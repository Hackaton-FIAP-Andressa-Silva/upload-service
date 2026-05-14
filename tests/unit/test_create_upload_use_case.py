import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.application.use_cases.create_upload_use_case import (
    CreateUploadUseCase,
    InvalidFileTypeError,
    FileTooLargeError,
    StorageError,
)
from src.domain.entities.upload import Upload, UploadStatus


@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda upload: upload)
    return repo


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.upload = AsyncMock(return_value="uploads/test-id/file.png")
    return storage


@pytest.fixture
def mock_messaging():
    messaging = AsyncMock()
    messaging.publish = AsyncMock(return_value=None)
    return messaging


@pytest.fixture
def use_case(mock_repository, mock_storage, mock_messaging):
    return CreateUploadUseCase(
        upload_repository=mock_repository,
        storage_port=mock_storage,
        messaging_port=mock_messaging,
    )


@pytest.mark.asyncio
async def test_create_upload_png_success(use_case, mock_repository, mock_storage, mock_messaging):
    content = b"\x89PNG\r\n\x1a\n" + b"fake-png-body"
    result = await use_case.execute("diagram.png", "image/png", content)

    assert result.status == "RECEIVED"
    assert result.filename == "diagram.png"
    assert result.upload_id is not None
    mock_storage.upload.assert_called_once()
    mock_repository.save.assert_called_once()
    mock_messaging.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_upload_pdf_success(use_case, mock_storage, mock_messaging):
    content = b"%PDF-1.4 fake-body"
    result = await use_case.execute("arch.pdf", "application/pdf", content)

    assert result.status == "RECEIVED"
    assert result.filename == "arch.pdf"


@pytest.mark.asyncio
async def test_create_upload_invalid_file_type(use_case):
    with pytest.raises(InvalidFileTypeError):
        await use_case.execute("file.txt", "text/plain", b"content")


@pytest.mark.asyncio
async def test_create_upload_file_too_large(use_case):
    huge_content = b"x" * (21 * 1024 * 1024)  # 21 MB
    with pytest.raises(FileTooLargeError):
        await use_case.execute("large.png", "image/png", huge_content)


@pytest.mark.asyncio
async def test_create_upload_storage_failure(use_case, mock_storage, mock_repository):
    mock_storage.upload = AsyncMock(side_effect=Exception("S3 unavailable"))
    valid_png = b"\x89PNG\r\n\x1a\n" + b"fake-body"

    with pytest.raises(StorageError):
        await use_case.execute("diagram.png", "image/png", valid_png)

    # Repository must NOT have been called
    mock_repository.save.assert_not_called()


@pytest.mark.asyncio
async def test_create_upload_jpeg_success(use_case):
    content = b"\xff\xd8\xff" + b"fake-jpeg-body"
    result = await use_case.execute("diagram.jpg", "image/jpeg", content)
    assert result.status == "RECEIVED"
