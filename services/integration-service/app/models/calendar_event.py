import uuid
from sqlalchemy import Column, String, Text, DATE, TIMESTAMP, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), nullable=False)
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    google_calendar_id = Column(String(255), nullable=True)
    google_event_id = Column(String(255), nullable=True)
    event_link = Column(Text, nullable=True)
    title = Column(String(1000), nullable=False)
    due_date = Column(DATE, nullable=True)
    sync_status = Column(String(50), nullable=False, default="pending")
    # sync_status: pending | success | failed
    error_message = Column(Text, nullable=True)
    retries = Column(Integer, default=0, nullable=False)
    synced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)
