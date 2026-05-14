import logging

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

from src.application.ports.storage_port import StoragePort
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)


class S3Storage(StoragePort):
    def __init__(self) -> None:
        self._session = aioboto3.Session()

    async def upload(self, key: str, content: bytes, content_type: str) -> str:
        async with self._session.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL,
        ) as s3:
            try:
                await s3.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                )
                logger.info("File uploaded to S3", extra={"s3_key": key, "bucket": settings.S3_BUCKET_NAME})
                return key
            except (BotoCoreError, ClientError) as exc:
                logger.error("S3 upload failed", extra={"s3_key": key, "error": str(exc)})
                raise
