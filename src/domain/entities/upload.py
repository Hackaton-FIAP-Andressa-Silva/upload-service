from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


class UploadStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    ERROR = "ERROR"


@dataclass
class Upload:
    id: str
    filename: str
    content_type: str
    s3_key: str
    file_size: int
    status: UploadStatus
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    @classmethod
    def create(cls, filename: str, content_type: str, s3_key: str, file_size: int) -> "Upload":
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            filename=filename,
            content_type=content_type,
            s3_key=s3_key,
            file_size=file_size,
            status=UploadStatus.RECEIVED,
            created_at=now,
            updated_at=now,
        )

    def update_status(self, status: UploadStatus, error_message: Optional[str] = None) -> None:
        self.status = status
        self.updated_at = datetime.utcnow()
        if error_message is not None:
            self.error_message = error_message
