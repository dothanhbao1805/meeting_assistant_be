from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# --- Participant ---
class ParticipantIn(BaseModel):
    user_id: UUID
    speaker_label: Optional[str] = None

class ParticipantOut(BaseModel):
    id: UUID
    user_id: UUID
    speaker_label: Optional[str]
    confirmed_by_ai: bool
    voice_match_score: Optional[float]

    class Config:
        from_attributes = True

# --- File ---
class MeetingFileOut(BaseModel):
    id: UUID
    storage_path: str
    storage_bucket: str
    file_type: Optional[str]
    file_size_bytes: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class MeetingCreate(BaseModel):
    title: str
    company_id: UUID
    scheduled_at: Optional[datetime] = None
    language_code: Optional[str] = "vi"
    participant_user_ids: Optional[List[UUID]] = []

class MeetingOut(BaseModel):
    id: UUID
    title: str
    company_id: UUID
    created_by_user_id: UUID
    status: str
    scheduled_at: Optional[datetime]
    duration_seconds: Optional[int]
    language_code: str
    created_at: datetime
    participants: List[ParticipantOut] = []
    files: List[MeetingFileOut] = []

    class Config:
        from_attributes = True