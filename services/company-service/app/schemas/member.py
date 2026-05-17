from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class MemberCreate(BaseModel):
    company_id: UUID
    account_id: UUID
    full_name: str
    role: str
    trello_user_id: Optional[str] = None
    trello_username: Optional[str] = None
    google_email: Optional[str] = None
    voice_embedding: Optional[List[float]] = None


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    trello_user_id: Optional[str] = None
    trello_username: Optional[str] = None
    google_email: Optional[str] = None


class MemberResponse(BaseModel):
    id: UUID
    company_id: UUID
    account_id: UUID
    full_name: str
    role: str
    trello_user_id: Optional[str]
    trello_username: Optional[str]
    google_email: Optional[str]
    voice_embedding: Optional[List[float]]
    joined_at: datetime

    class Config:
        from_attributes = True

class MemberListResponse(BaseModel):
    items: List[MemberResponse]
    total: int
    page: int
    page_size: int