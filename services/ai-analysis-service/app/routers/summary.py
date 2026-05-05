import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.summary_repo import MeetingSummaryRepo
from app.repositories.job_repo import AnalysisJobRepo
from app.schemas.summary import (
    SummaryResponse,
    SummaryUpdate,
    SummaryRegenerateRequest,
    SummaryRegenerateResponse,
)
from app.core.redis import redis_client, QUEUE_ANALYSIS
from app.core.config import settings

router = APIRouter(tags=["Summaries"])


@router.get("/meetings/{meeting_id}/summary", response_model=SummaryResponse)
async def get_summary_by_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingSummaryRepo(db)
    summary = await repo.get_by_meeting_id(meeting_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary không tồn tại cho meeting này")
    return summary


@router.patch("/summaries/{summary_id}", response_model=SummaryResponse)
async def update_summary(
    summary_id: uuid.UUID,
    payload: SummaryUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingSummaryRepo(db)
    summary = await repo.get_by_id(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary không tồn tại")

    update_data = payload.model_dump(exclude_unset=True)
    update_data["is_edited"] = True
    
    updated = await repo.update(summary_id, update_data)
    return updated


@router.post("/summaries/{summary_id}/regenerate", response_model=SummaryRegenerateResponse)
async def regenerate_summary(
    summary_id: uuid.UUID,
    payload: SummaryRegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    summary_repo = MeetingSummaryRepo(db)
    job_repo = AnalysisJobRepo(db)
    
    summary = await summary_repo.get_by_id(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary không tồn tại")
    
    # Tạo job mới để regenerate
    # Chúng ta cần transcript_id từ job cũ
    old_job = await job_repo.get_by_id(summary.analysis_job_id)
    if not old_job:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin job cũ")

    new_job = await job_repo.create({
        "meeting_id": summary.meeting_id,
        "transcript_id": old_job.transcript_id,
        "model": old_job.model,
    })
    
    # Gửi message vào queue với hint
    message = {
        "job_id": str(new_job.id),
        "meeting_id": str(new_job.meeting_id),
        "transcript_id": str(new_job.transcript_id),
        "prompt_hint": payload.prompt_hint,
        "type": "regenerate_summary"
    }
    await redis_client.lpush(QUEUE_ANALYSIS, json.dumps(message))
    
    return SummaryRegenerateResponse(new_job_id=new_job.id, status="queued")
