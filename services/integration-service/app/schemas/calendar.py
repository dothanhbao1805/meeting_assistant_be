from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.trello import ConfirmedTask


class CalendarSyncRequest(BaseModel):
    meeting_id: UUID
    company_id: UUID
    confirmed_tasks: List[ConfirmedTask]


class CalendarSyncResult(BaseModel):
    task_id: UUID
    google_event_id: Optional[str] = None
    event_link: Optional[str] = None
    status: str
    error: Optional[str] = None


class CalendarSyncResponse(BaseModel):
    synced_count: int
    failed_count: int
    results: List[CalendarSyncResult]
