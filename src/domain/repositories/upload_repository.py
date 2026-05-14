from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.upload import Upload


class UploadRepository(ABC):
    @abstractmethod
    async def save(self, upload: Upload) -> Upload:
        ...

    @abstractmethod
    async def find_by_id(self, upload_id: str) -> Optional[Upload]:
        ...

    @abstractmethod
    async def update(self, upload: Upload) -> Upload:
        ...
