import uuid
from sqlalchemy import Column, String, Text, Float, ForeignKey, TIMESTAMP, DATE, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.database import Base


class ExtractedTask(Base):
    __tablename__ = "extracted_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_job_id = Column(
        UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=False
    )
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    raw_assignee_text = Column(String(255), nullable=True)
    resolved_user_id = Column(UUID(as_uuid=True), nullable=True)
    deadline_raw = Column(String(255), nullable=True)
    deadline_date = Column(DATE, nullable=True)
    priority = Column(String(20), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    source_utterance_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    manually_assigned = Column(Boolean, default=False)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    rejected_at = Column(TIMESTAMP(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)

    job = relationship("AnalysisJob", back_populates="tasks")
