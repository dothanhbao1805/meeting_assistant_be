from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional, List


class TaskResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    title: str
    description: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


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
