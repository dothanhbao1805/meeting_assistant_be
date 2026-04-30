from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.task import CreateTaskRequest, TaskResponse
from app.repositories.task_repo import TaskRepo
from app.services.task_service import TaskService
import uuid

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service(db: AsyncSession = Depends(get_db)):
    return TaskService(TaskRepo(db))


@router.post("", response_model=TaskResponse)
async def create_task(
    payload: CreateTaskRequest,
    service: TaskService = Depends(get_task_service),
):
    return await service.create_task(payload)

@router.post("/{meeting_id}/confirm-all")
async def confirm_all_tasks(
    meeting_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    result = await service.confirm_all_tasks(meeting_id)
    return result

@router.post("/{meeting_id}/sync")
async def sync_tasks(
    meeting_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    return await service.sync_to_integration(meeting_id)

    
