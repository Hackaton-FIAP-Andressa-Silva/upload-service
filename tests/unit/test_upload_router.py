import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from src.api.routers.upload_router import (
    router,
    get_create_use_case,
    get_status_use_case,
    get_update_status_use_case,
)
from src.application.dtos.upload_dto import UploadDTO, UploadStatusDTO
from src.infrastructure.config import settings

VALID_UUID = "a1b2c3d4-e5f6-4789-abcd-ef0123456789"
FIXED_DT = datetime(2026, 5, 14, 10, 0, 0)


def _make_upload_dto():
    return UploadDTO(
        upload_id=VALID_UUID,
        status="RECEIVED",
        filename="arch.png",
        created_at=FIXED_DT,
    )


def _make_status_dto(status="ANALYZED", error_message=None):
    return UploadStatusDTO(
        upload_id=VALID_UUID,
        status=status,
        filename="arch.png",
        created_at=FIXED_DT,
        updated_at=FIXED_DT,
        error_message=error_message,
    )


@pytest.fixture
def mock_create_uc():
    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=_make_upload_dto())
    return uc


@pytest.fixture
def mock_status_uc():
    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=_make_status_dto())
    return uc


@pytest.fixture
def mock_update_uc():
    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=_make_status_dto(status="ERROR", error_message="failed"))
    return uc


@pytest.fixture
def test_app(mock_create_uc, mock_status_uc, mock_update_uc):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_create_use_case] = lambda: mock_create_uc
    app.dependency_overrides[get_status_use_case] = lambda: mock_status_uc
    app.dependency_overrides[get_update_status_use_case] = lambda: mock_update_uc
    return app


@pytest.mark.asyncio
async def test_upload_success(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/uploads",
            files={"file": ("arch.png", b"\x89PNG\r\n\x1a\n" + b"body", "image/png")},
        )
    assert response.status_code == 202
    body = response.json()
    assert body["upload_id"] == VALID_UUID
    assert body["status"] == "RECEIVED"
    assert body["filename"] == "arch.png"


@pytest.mark.asyncio
async def test_get_status_success(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/uploads/{VALID_UUID}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ANALYZED"
    assert body["upload_id"] == VALID_UUID


@pytest.mark.asyncio
async def test_get_status_invalid_uuid(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/api/v1/uploads/not-a-uuid/status")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_UUID"


@pytest.mark.asyncio
async def test_update_status_success(test_app):
    token = settings.INTERNAL_SERVICE_TOKEN
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/uploads/{VALID_UUID}/status",
            json={"status": "ERROR", "error_message": "failed"},
            headers={"X-Internal-Token": token},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "ERROR"


@pytest.mark.asyncio
async def test_update_status_wrong_token(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/uploads/{VALID_UUID}/status",
            json={"status": "ANALYZED"},
            headers={"X-Internal-Token": "totally-wrong-token-xyz"},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_update_status_missing_token(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/uploads/{VALID_UUID}/status",
            json={"status": "ANALYZED"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_status_invalid_uuid(test_app):
    token = settings.INTERNAL_SERVICE_TOKEN
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.patch(
            "/api/v1/uploads/not-a-uuid/status",
            json={"status": "ANALYZED"},
            headers={"X-Internal-Token": token},
        )
    assert response.status_code == 400
