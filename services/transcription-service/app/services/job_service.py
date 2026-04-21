import uuid
import json
from fastapi import HTTPException
from app.repositories.job_repo import TranscriptionJobRepo
from app.models.transcription_job import TranscriptionJob
from app.core.redis import redis_client, QUEUE_TRANSCRIPTION

MAX_RETRY = 3


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

    async def retry_job(self, job_id: uuid.UUID) -> TranscriptionJob:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job không tồn tại")
        # Chỉ retry khi status = failed
        if job.status != "failed":
            raise HTTPException(
                status_code=400,
                detail=f"Chỉ retry được job có status 'failed', hiện tại: '{job.status}'",
            )
        # Kiểm tra số lần retry
        retry_count = await self.repo.get_retry_count(job_id)
        if retry_count >= MAX_RETRY:
            raise HTTPException(
                status_code=400,
                detail=f"Job đã retry {retry_count} lần, vượt quá giới hạn {MAX_RETRY} lần",
            )
        # Reset job về queued
        job = await self.repo.reset_for_retry(job_id, retry_number=retry_count + 1)
        # Push lại vào queue
        message = {
            "meeting_id": str(job.meeting_id),
            "media_file_id": str(job.media_file_id),
            "job_id": str(job.id),  # truyền job_id để worker không tạo job mới
        }
        await redis_client.lpush(QUEUE_TRANSCRIPTION, json.dumps(message))

        return job
