from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date


class ConfirmedTask(BaseModel):
    task_id: UUID
    title: str
    description: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = "medium"


class TrelloSyncRequest(BaseModel):
    meeting_id: UUID
    company_id: UUID
    trello_board_id: str
    trello_list_id: str
    confirmed_tasks: List[ConfirmedTask]


class TrelloSyncResult(BaseModel):
    task_id: UUID
    trello_card_id: Optional[str] = None
    trello_card_url: Optional[str] = None
    status: str  # success / failed
    error: Optional[str] = None


class TrelloSyncResponse(BaseModel):
    synced_count: int
    failed_count: int
    results: List[TrelloSyncResult]
