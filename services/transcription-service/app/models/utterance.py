import uuid
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Boolean
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
    original_text = Column(Text, nullable=True)   # lưu bản gốc trước khi sửa
    is_edited = Column(Boolean, default=False, nullable=False)
    start_time_ms = Column(Integer, nullable=True)
    end_time_ms = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    sequence_order = Column(Integer, nullable=True)

    transcript = relationship("Transcript", back_populates="utterances")
