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
    priority: Optional[str] = None  # low / medium / high
    status: str  # pending / completed

class CreateTaskRequest(BaseModel):
    meeting_id: UUID
    title: str
    description: Optional[str] = None
    resolved_user_id: Optional[UUID] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None  # low / medium / high
    
class SkippedTask(BaseModel):
    task_id: UUID
    missing_fields: List[str]


class ConfirmTasksResponse(BaseModel):
    confirmed_count: int
    skipped_count: int
    skipped_tasks: List[SkippedTask] = []