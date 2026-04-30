from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ─── Utterance Schemas ───────────────────────────────────────────────────────

class UtteranceResponse(BaseModel):
    id: UUID
    transcript_id: UUID
    speaker_label: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    text: str
    original_text: Optional[str] = None
    is_edited: bool = False
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None
    confidence: Optional[float] = None
    sequence_order: Optional[int] = None

    model_config = {"from_attributes": True}


class UtteranceListResponse(BaseModel):
    items: List[UtteranceResponse]
    total: int
    page: int
    limit: int
    has_next: bool


class UtteranceUpdateRequest(BaseModel):
    text: str


class UtteranceResolveSpeakerRequest(BaseModel):
    resolved_user_id: UUID
    apply_to_all_same_label: bool = False


class UtteranceResolveSpeakerResponse(BaseModel):
    updated_count: int
    message: str


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
    

class UtteranceUpdateResolved(BaseModel):
    speaker_label: str
    resolved_user_id: UUID