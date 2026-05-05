import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SummaryResponse(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    summary_text: Optional[str]
    edited_summary: Optional[str]
    is_edited: Optional[bool] = False
    key_decisions: List[str]
    topics_covered: List[str]
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SummaryUpdate(BaseModel):
    edited_summary: str
    key_decisions: Optional[List[str]] = None


class SummaryRegenerateRequest(BaseModel):
    prompt_hint: Optional[str] = None


class SummaryRegenerateResponse(BaseModel):
    new_job_id: uuid.UUID
    status: str
