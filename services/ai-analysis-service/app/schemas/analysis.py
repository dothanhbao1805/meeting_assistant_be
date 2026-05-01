# schemas/analysis.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class SummaryResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    summary_text: Optional[str] = None
    edited_summary: Optional[str] = None
    key_decisions: Optional[list[str]] = None
    attendees_mentioned: Optional[list[str]] = None
    topics_covered: Optional[list[str]] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    title: str
    description: Optional[str] = None
    raw_assignee_text: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    deadline_raw: Optional[str] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None
    status: str
    ai_confidence: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MeetingAnalysisResponse(BaseModel):
    status: str
    summary: Optional[SummaryResponse] = None
    tasks: list[TaskResponse] = []
    unresolved_speakers: Optional[list[str]] = None
