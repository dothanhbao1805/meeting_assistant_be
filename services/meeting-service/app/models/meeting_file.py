import uuid
from sqlalchemy import Column, String, Integer, BigInteger, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import MeetingBase

class MeetingFile(MeetingBase):
    __tablename__ = "meeting_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    storage_path = Column(Text, nullable=False)   # Supabase path
    storage_bucket = Column(String(100), nullable=False)
    file_type = Column(String(10))                # mp4, mp3, wav...
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Integer)
    checksum_sha256 = Column(String(64))
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default="now()")

    meeting = relationship("Meeting", back_populates="files")
