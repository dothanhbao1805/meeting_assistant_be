import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.redis import redis_client, QUEUE_ANALYSIS
from app.core.config import settings
from app.repositories.job_repo import AnalysisJobRepo
from app.schemas.job import AnalysisJobCreate, AnalysisJobResponse

router = APIRouter(prefix="/analysis-jobs", tags=["Analysis Jobs"])


@router.post("/", response_model=AnalysisJobResponse, status_code=201)
async def create_analysis_job(
    payload: AnalysisJobCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = AnalysisJobRepo(db)

    # Idempotency — tránh tạo duplicate job
    existing = await repo.get_by_meeting_and_transcript(
        meeting_id=payload.meeting_id,
        transcript_id=payload.transcript_id,
    )
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Job đã tồn tại cho transcript này: {existing.id}"
        )

    # Tạo job
    job = await repo.create(
        {
            "meeting_id": payload.meeting_id,
            "transcript_id": payload.transcript_id,
            "model": payload.model or settings.GROQ_MODEL,
        }
    )

    # Push vào queue
    message = {
        "job_id": str(job.id),
        "meeting_id": str(job.meeting_id),
        "transcript_id": str(job.transcript_id),
    }
    await redis_client.lpush(QUEUE_ANALYSIS, json.dumps(message))

    return job


@router.get("/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = AnalysisJobRepo(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
    return job


@router.post("/{job_id}/retry", response_model=AnalysisJobResponse, status_code=202)
async def retry_analysis_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = AnalysisJobRepo(db)

    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job không tồn tại")

    if job.status != "failed":
        raise HTTPException(
            status_code=409,
            detail=f"Chỉ có thể retry job ở trạng thái failed, job hiện tại: {job.status}",
        )

    # Reset job về queued
    job = await repo.update(
        job,
        status="queued",
        error_message=None,
        input_tokens=None,
        output_tokens=None,
        completed_at=None,
    )

    # Push lại vào queue
    message = {
        "job_id": str(job.id),
        "meeting_id": str(job.meeting_id),
        "transcript_id": str(job.transcript_id),
    }
    await redis_client.lpush(QUEUE_ANALYSIS, json.dumps(message))

    return job
