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
