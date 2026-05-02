import uuid
from sqlalchemy import Column, String, Text, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class TrelloSyncLog(Base):
    __tablename__ = "trello_sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), nullable=False)
    meeting_id = Column(UUID(as_uuid=True), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    trello_board_id = Column(String(100), nullable=True)
    trello_list_id = Column(String(100), nullable=True)
    trello_card_id = Column(String(100), nullable=True)
    trello_card_url = Column(Text, nullable=True)
    assigned_trello_user_id = Column(String(100), nullable=True)
    sync_status = Column(String(50), nullable=False, default="pending")
    # sync_status: pending | success | failed
    error_message = Column(Text, nullable=True)
    retries = Column(Integer, default=0, nullable=False)
    synced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)
