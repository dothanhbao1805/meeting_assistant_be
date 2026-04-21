import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transcription_job import TranscriptionJob


class TranscriptionJobRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> TranscriptionJob:
        job = TranscriptionJob(
            meeting_id=uuid.UUID(data["meeting_id"]),
            media_file_id=uuid.UUID(data["media_file_id"]),
            status=data.get("status", "queued"),
            model=data.get("model", "nova-2"),
            options=data.get("options", {}),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> TranscriptionJob | None:
        result = await self.db.execute(
            select(TranscriptionJob).where(TranscriptionJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_deepgram_request_id(
        self, deepgram_request_id: str
    ) -> TranscriptionJob | None:
        """Tìm job theo deepgram_request_id (dùng cho webhook)"""
        result = await self.db.execute(
            select(TranscriptionJob).where(
                TranscriptionJob.deepgram_request_id == deepgram_request_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_meeting_id(self, meeting_id: uuid.UUID) -> list[TranscriptionJob]:
        result = await self.db.execute(
            select(TranscriptionJob)
            .where(TranscriptionJob.meeting_id == meeting_id)
            .order_by(TranscriptionJob.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_meeting_and_file(
        self,
        meeting_id: str,
        media_file_id: str,
    ) -> TranscriptionJob | None:
        result = await self.db.execute(
            select(TranscriptionJob).where(
                TranscriptionJob.meeting_id == uuid.UUID(meeting_id),
                TranscriptionJob.media_file_id == uuid.UUID(media_file_id),
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: str,
        error_message: str | None = None,
    ) -> TranscriptionJob | None:
        job = await self.get_by_id(job_id)
        if not job:
            return None
        job.status = status
        if error_message:
            job.error_message = error_message
        await self.db.commit()
        await self.db.refresh(job)
        return job


async def get_retry_count(self, job_id: uuid.UUID) -> int:
    """Đếm số lần đã retry dựa vào error_message có prefix 'retry:'"""
    job = await self.get_by_id(job_id)
    if not job or not job.error_message:
        return 0
    retries = [
        line for line in job.error_message.splitlines() if line.startswith("retry:")
    ]
    return len(retries)


async def reset_for_retry(
    self,
    job_id: uuid.UUID,
    retry_number: int,
) -> TranscriptionJob | None:
    job = await self.get_by_id(job_id)
    if not job:
        return None
    job.status = "queued"
    job.deepgram_request_id = None
    job.processing_ms = None
    job.started_at = None
    job.completed_at = None
    # Ghi lại lịch sử retry vào error_message
    history = job.error_message or ""
    job.error_message = history + f"\nretry:{retry_number}"
    await self.db.commit()
    await self.db.refresh(job)
    return job
