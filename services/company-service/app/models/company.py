from sqlalchemy import String, Text, DateTime, Enum
import enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional

from app.db.database import Base


# ENUM
class CompanyStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    trello_token: Mapped[Optional[str]] = mapped_column(Text)
    trello_api_key: Mapped[Optional[str]] = mapped_column(Text)
    trello_workspace_id: Mapped[Optional[str]] = mapped_column(String(100))
    # TODO: encrypt OAuth tokens at rest when a project-wide encryption utility is available.
    google_access_token: Mapped[Optional[str]] = mapped_column(Text)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    google_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime)
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String)

    owner_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus), default=CompanyStatus.active
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # relationship
    members: Mapped[List["Member"]] = relationship(
        "Member", back_populates="company", cascade="all, delete-orphan"
    )
