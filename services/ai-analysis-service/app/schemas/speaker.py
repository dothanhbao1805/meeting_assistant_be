from pydantic import BaseModel
from uuid import UUID

class SpeakerResolveRequest(BaseModel):
    speaker_label: str
    resolved_user_id: UUID