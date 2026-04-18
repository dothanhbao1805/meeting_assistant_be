import uuid
from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import MeetingBase

class Meeting(MeetingBase):
    __tablename__ = "meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(500), nullable=False)
    trello_board_id = Column(String(100))
    trello_board_name = Column(String(255))
    trello_list_id = Column(String(100))
    status = Column(String(50), default="uploaded")
    scheduled_at = Column(TIMESTAMP(timezone=True))
    duration_seconds = Column(Integer)
    language_code = Column(String(10), default="vi")
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()")
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()")

    participants = relationship("MeetingParticipant", back_populates="meeting")
    files = relationship("MeetingFile", back_populates="meeting")
