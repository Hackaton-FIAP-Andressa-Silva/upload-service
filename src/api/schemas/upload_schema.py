from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: str
    status: str
    filename: str
    created_at: datetime


class UploadStatusResponse(BaseModel):
    upload_id: str
    status: str
    filename: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str
    error_message: Optional[str] = None
