import json
import logging

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

from src.application.ports.messaging_port import MessagingPort
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class SQSPublisher(MessagingPort):
    def __init__(self) -> None:
        self._session = aioboto3.Session()

    async def publish(
        self,
        upload_id: str,
        s3_key: str,
        filename: str,
        content_type: str,
    ) -> None:
        message = {
            "upload_id": upload_id,
            "s3_key": s3_key,
            "filename": filename,
            "content_type": content_type,
        }

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                async with self._session.client(
                    "sqs",
                    region_name=settings.AWS_REGION,
                    endpoint_url=settings.AWS_ENDPOINT_URL,
                ) as sqs:
                    await sqs.send_message(
                        QueueUrl=settings.SQS_QUEUE_URL,
                        MessageBody=json.dumps(message),
                    )
                    logger.info(
                        "Message published to SQS",
                        extra={"upload_id": upload_id, "queue": settings.SQS_QUEUE_URL},
                    )
                    return
            except (BotoCoreError, ClientError) as exc:
                logger.warning(
                    "SQS publish attempt failed",
                    extra={"attempt": attempt, "upload_id": upload_id, "error": str(exc)},
                )
                if attempt > MAX_RETRIES:
                    logger.error("SQS publish failed after retries", extra={"upload_id": upload_id})
                    raise
