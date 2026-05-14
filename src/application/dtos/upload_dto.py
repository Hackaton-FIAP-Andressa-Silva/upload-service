from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.entities.upload import UploadStatus


@dataclass
class UploadDTO:
    upload_id: str
    status: str
    filename: str
    created_at: datetime


@dataclass
class UploadStatusDTO:
    upload_id: str
    status: str
    filename: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str]
