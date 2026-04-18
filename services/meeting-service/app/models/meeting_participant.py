import uuid
from sqlalchemy import Column, String, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import MeetingBase

class MeetingParticipant(MeetingBase):
    __tablename__ = "meeting_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    speaker_label = Column(String(50))
    confirmed_by_ai = Column(Boolean, default=False)
    voice_match_score = Column(Float)

    meeting = relationship("Meeting", back_populates="participants")