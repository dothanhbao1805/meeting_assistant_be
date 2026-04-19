import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repositories.job_repo import TranscriptionJobRepo
from app.services.job_service import TranscriptionJobService
from app.schemas.job import TranscriptionJobResponse

router = APIRouter(prefix="/transcription-jobs", tags=["Transcription Jobs"])


def get_job_service(db: AsyncSession = Depends(get_db)) -> TranscriptionJobService:
    repo = TranscriptionJobRepo(db)
    return TranscriptionJobService(repo)


@router.get("/{job_id}", response_model=TranscriptionJobResponse)
async def get_job(
    job_id: uuid.UUID,
    service: TranscriptionJobService = Depends(get_job_service),
):
    return await service.get_job(job_id)


@router.get("/", response_model=list[TranscriptionJobResponse])
async def get_jobs_by_meeting(
    meeting_id: uuid.UUID,
    service: TranscriptionJobService = Depends(get_job_service),
):
    return await service.get_jobs_by_meeting(meeting_id)
