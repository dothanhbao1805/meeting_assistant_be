import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("transcription_jobs.id"), nullable=False
    )
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    full_text = Column(Text, nullable=True)
    edited_text = Column(Text, nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    speaker_count = Column(Integer, nullable=True)
    confidence_avg = Column(Float, nullable=True)
    language_detected = Column(String(10), nullable=True)
    raw_deepgram_response = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)

    job = relationship("TranscriptionJob", back_populates="transcripts")
    utterances = relationship("Utterance", back_populates="transcript")
