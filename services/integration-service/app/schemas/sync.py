from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SyncQueueItem(BaseModel):
    id: UUID
    meeting_id: UUID
    job_type: str
    payload: dict[str, Any] | None = None
    status: str
    scheduled_at: datetime | None = None
    processed_at: datetime | None = None
    attempts: int
    max_attempts: int


class SyncQueueResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SyncQueueItem]


class SyncStatusSection(BaseModel):
    total: int
    by_status: dict[str, int]


class SyncQueueStatusSection(SyncStatusSection):
    items: list[SyncQueueItem]


class SyncStatusResponse(BaseModel):
    meeting_id: UUID
    overall_status: str
    queue: SyncQueueStatusSection
    trello: SyncStatusSection
    calendar: SyncStatusSection
