from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class MeetingFileResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    storage_path: str
    storage_bucket: str
    file_type: str
    file_size_bytes: int
    duration_seconds: Optional[int] = None  
    checksum_sha256: str
    uploaded_at: datetime    
                   
    class Config:
        from_attributes = True              