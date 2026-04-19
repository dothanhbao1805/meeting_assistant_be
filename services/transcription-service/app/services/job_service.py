import uuid
from fastapi import HTTPException
from app.repositories.job_repo import TranscriptionJobRepo
from app.models.transcription_job import TranscriptionJob


class TranscriptionJobService:
    def __init__(self, repo: TranscriptionJobRepo):
        self.repo = repo

    async def get_job(self, job_id: uuid.UUID) -> TranscriptionJob:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job không tồn tại")
        return job

    async def get_jobs_by_meeting(
        self, meeting_id: uuid.UUID
    ) -> list[TranscriptionJob]:
        return await self.repo.get_by_meeting_id(meeting_id)
