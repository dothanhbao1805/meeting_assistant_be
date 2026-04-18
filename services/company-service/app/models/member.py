from sqlalchemy import String, DateTime, Enum, ForeignKey
import enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import Optional, List

from app.db.database import Base


# ENUM
class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id")
    )

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    full_name: Mapped[str] = mapped_column(String(255))

    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole), default=MemberRole.member
    )

    trello_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trello_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    google_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    voice_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(512), nullable=True)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # relationship
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="members"
    )