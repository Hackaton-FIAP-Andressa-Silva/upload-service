from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "upload-service"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/upload_db"

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: Optional[str] = None  # For LocalStack
    S3_BUCKET_NAME: str = "architecture-diagrams"
    SQS_QUEUE_URL: str = "http://localhost:4566/000000000000/diagram-analysis-queue"

    # API Key (internal service token for status updates)
    INTERNAL_SERVICE_TOKEN: str = "internal-changeme"

    class Config:
        env_file = ".env"


settings = Settings()
