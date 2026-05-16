import uuid
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class TranscriptionJob(Base):
    __tablename__ = "transcription_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    media_file_id = Column(UUID(as_uuid=True), nullable=False)
    deepgram_request_id = Column(String(200), nullable=True)
    status = Column(String(50), nullable=False, default="queued")
    # status: queued | processing | done | failed
    model = Column(String(100), nullable=True)
    options = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_ms = Column(Integer, nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    company_id = Column(UUID(as_uuid=True), nullable=True)

    transcripts = relationship("Transcript", back_populates="job")
