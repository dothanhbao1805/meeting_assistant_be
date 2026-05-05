from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional, List


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
    source_utterance_ids: Optional[List[UUID]] = None
    manually_assigned: Optional[bool] = False
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    source_utterances: List[dict] = []


class TaskRejectRequest(BaseModel):
    reason: Optional[str] = None


class CreateTaskRequest(BaseModel):
    meeting_id: UUID
    title: str
    description: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None


class SkippedTask(BaseModel):
    task_id: UUID
    missing_fields: List[str]


class ConfirmTasksResponse(BaseModel):
    confirmed_count: int
    skipped_count: int
    skipped_tasks: List[SkippedTask] = []


class SyncResponse(BaseModel):
    status: str
    synced_count: int = 0
    message: Optional[str] = None
