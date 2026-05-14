import pytest


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Ensure tests run with predictable environment."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("SQS_QUEUE_URL", "http://localhost:4566/000000000000/test-queue")
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "test-token")
