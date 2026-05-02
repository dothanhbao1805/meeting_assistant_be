import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.task_repo import TaskRepo
from app.schemas.task import (
    CreateTaskRequest,
    TaskResponse,
    TaskUpdate,
    ConfirmTasksResponse,
    SyncResponse,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service(db: AsyncSession = Depends(get_db)):
    return TaskService(TaskRepo(db))


@router.post("", response_model=TaskResponse)
async def create_task(
    payload: CreateTaskRequest,
    service: TaskService = Depends(get_task_service),
):
    return await service.create_task(payload)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    return await service.update_task(task_id, payload.model_dump(exclude_unset=True))


@router.post("/{meeting_id}/confirm-all", response_model=ConfirmTasksResponse)
async def confirm_all_tasks(
    meeting_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    return await service.confirm_all_tasks(meeting_id)


@router.post("/{meeting_id}/sync", response_model=SyncResponse)
async def sync_tasks(
    meeting_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    return await service.sync_to_integration(meeting_id)
