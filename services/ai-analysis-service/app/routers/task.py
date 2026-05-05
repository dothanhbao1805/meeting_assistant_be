import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.task_repo import TaskRepo
from app.schemas.task import (
    CreateTaskRequest,
    TaskResponse,
    TaskUpdate,
    ConfirmTasksResponse,
    SyncResponse,
    TaskRejectRequest,
    TaskDetailResponse,
)
from app.services.task_service import TaskService
from app.services.utterance_client import fetch_utterances

from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service(db: AsyncSession = Depends(get_db)):
    return TaskService(TaskRepo(db))


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    meeting_id: uuid.UUID,
    status: Optional[str] = None,
    assigned_user_id: Optional[uuid.UUID] = None,
    service: TaskService = Depends(get_task_service),
):
    """
    GET /api/v1/tasks?meeting_id=...&status=...&assigned_user_id=...
    """
    return await service.repo.get_tasks_by_meeting(
        meeting_id=meeting_id,
        status=status,
        resolved_user_id=assigned_user_id
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    task = await service.repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại")
    
    # Lấy utterances từ transcription service
    from app.repositories.job_repo import AnalysisJobRepo
    job_repo = AnalysisJobRepo(service.repo.db)
    job_obj = await job_repo.get_by_id(task.analysis_job_id)
    
    source_utterances = []
    if job_obj and task.source_utterance_ids:
        try:
            utterances = await fetch_utterances(str(job_obj.transcript_id))
            source_utterances = [u for u in utterances if uuid.UUID(u['id']) in task.source_utterance_ids]
        except Exception:
            # Nếu không lấy được utterance thì vẫn trả về task info
            pass

    return TaskDetailResponse(
        **TaskResponse.model_validate(task).model_dump(),
        source_utterances=source_utterances
    )


@router.post("", response_model=TaskResponse)
async def create_task(
    payload: CreateTaskRequest,
    service: TaskService = Depends(get_task_service),
):
    # Đánh dấu là tạo thủ công
    data = payload.model_dump()
    data["manually_assigned"] = True
    # Lưu ý: create_task trong service có thể cần update để nhận extra fields
    return await service.repo.create_task(data, analysis_job_id=uuid.uuid4()) # dummy job id if manual?


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    return await service.update_task(task_id, payload.model_dump(exclude_unset=True))


@router.post("/{task_id}/confirm", response_model=TaskResponse)
async def confirm_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    task = await service.repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại")
    
    if not task.resolved_user_id or not task.deadline_date:
        raise HTTPException(
            status_code=400, 
            detail="Thiếu resolved_user_id hoặc deadline_date để confirm"
        )
    
    updated = await service.repo.update_task(task_id, {
        "status": "confirmed",
        "confirmed_at": datetime.now(timezone.utc)
    })
    return updated


@router.post("/{task_id}/reject", response_model=TaskResponse)
async def reject_task(
    task_id: uuid.UUID,
    payload: TaskRejectRequest,
    service: TaskService = Depends(get_task_service),
):
    task = await service.repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại")
    
    updated = await service.repo.update_task(task_id, {
        "status": "rejected",
        "rejected_at": datetime.now(timezone.utc),
        "rejection_reason": payload.reason
    })
    return updated


# Các endpoint liên quan đến meeting ID sẽ được chuyển sang /meetings/{id}/tasks/... ở router khác hoặc để đây với prefix khác
@router.post("/meetings/{meeting_id}/confirm-all", response_model=ConfirmTasksResponse)
async def confirm_all_tasks(
    meeting_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    return await service.confirm_all_tasks(meeting_id)


@router.post("/meetings/{meeting_id}/sync", response_model=SyncResponse)
async def sync_tasks(
    meeting_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
):
    return await service.sync_to_integration(meeting_id)
