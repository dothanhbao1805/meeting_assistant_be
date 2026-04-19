from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class TranscriptionJobResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    media_file_id: UUID
    deepgram_request_id: Optional[str] = None
    status: str
    model: Optional[str] = None
    options: Optional[dict] = None
    error_message: Optional[str] = None
    processing_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
