import uuid
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_job_id = Column(
        UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=False
    )
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    summary_text = Column(Text, nullable=True)
    edited_summary = Column(Text, nullable=True)
    key_decisions = Column(JSONB, nullable=True)
    attendees_mentioned = Column(JSONB, nullable=True)
    topics_covered = Column(JSONB, nullable=True)
    language = Column(String(10), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)

    job = relationship("AnalysisJob", back_populates="summary")
