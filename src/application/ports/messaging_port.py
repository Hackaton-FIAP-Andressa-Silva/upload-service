from abc import ABC, abstractmethod


class MessagingPort(ABC):
    @abstractmethod
    async def publish(
        self,
        upload_id: str,
        s3_key: str,
        filename: str,
        content_type: str,
    ) -> None:
        """Publish a diagram analysis job to the message queue."""
        ...
