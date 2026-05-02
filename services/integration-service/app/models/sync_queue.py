import uuid
from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base


class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    job_type = Column(String(50), nullable=False)
    # job_type: trello | calendar
    payload = Column(JSONB, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    # status: pending | processing | done | failed
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
