from sqlalchemy import Column, String, BigInteger, Text, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class UploadModel(Base):
    __tablename__ = "uploads"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    s3_key = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    status = Column(String(50), nullable=False, default="RECEIVED")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
