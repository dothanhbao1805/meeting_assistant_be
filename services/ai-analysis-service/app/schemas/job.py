from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AnalysisJobCreate(BaseModel):
    meeting_id: UUID
    transcript_id: UUID
    model: Optional[str] = "llama-3.3-70b-versatile"


class AnalysisJobResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    transcript_id: UUID
    status: str
    ai_model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
