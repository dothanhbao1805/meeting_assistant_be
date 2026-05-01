from pydantic import BaseModel
from uuid import UUID


class AutoResolveRequest(BaseModel):
    company_id: UUID
    meeting_id: UUID
    meeting_file_id: UUID

class AutoResolveResponse(BaseModel):
    transcript_id: UUID
    speakers_processed: int
    speakers_resolved: int
    utterances_resolved: int
    detail: dict