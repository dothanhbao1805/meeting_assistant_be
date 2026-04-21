from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.utterance import UtteranceResponse




# ─── Transcript Schemas ───────────────────────────────────────────────────────

class TranscriptResponse(BaseModel):
    id: UUID
    job_id: UUID
    meeting_id: UUID
    full_text: Optional[str] = None
    edited_text: Optional[str] = None
    is_edited: bool = False
    speaker_count: Optional[int] = None
    confidence_avg: Optional[float] = None
    language_detected: Optional[str] = None
    created_at: Optional[datetime] = None
    utterances: List[UtteranceResponse] = []

    model_config = {"from_attributes": True}


class TranscriptUpdateRequest(BaseModel):
    edited_text: str


class MeetingTranscriptResponse(BaseModel):
    job_id: UUID
    job_status: str
    transcript: Optional[TranscriptResponse] = None
    message: Optional[str] = None