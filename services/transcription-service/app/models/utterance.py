import uuid
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base


class Utterance(Base):
    __tablename__ = "utterances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcript_id = Column(
        UUID(as_uuid=True), ForeignKey("transcripts.id"), nullable=False
    )
    speaker_label = Column(String(50), nullable=True)  # Speaker_0, Speaker_1...
    resolved_user_id = Column(UUID(as_uuid=True), nullable=True)
    text = Column(Text, nullable=False)
    start_time_ms = Column(Integer, nullable=True)
    end_time_ms = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    sequence_order = Column(Integer, nullable=True)

    transcript = relationship("Transcript", back_populates="utterances")
