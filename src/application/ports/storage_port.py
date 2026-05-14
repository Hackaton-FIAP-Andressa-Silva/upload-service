from abc import ABC, abstractmethod


class StoragePort(ABC):
    @abstractmethod
    async def upload(self, key: str, content: bytes, content_type: str) -> str:
        """Upload file and return the S3 key."""
        ...
