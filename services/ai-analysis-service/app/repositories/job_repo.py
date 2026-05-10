import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.analysis_job import AnalysisJob


class AnalysisJobRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> AnalysisJob:
        job = AnalysisJob(
            meeting_id=data["meeting_id"],
            transcript_id=data["transcript_id"],
            company_id=data.get("company_id"),  # thêm
            status="queued",
            ai_model=data.get("ai_model")
            or data.get("model", "llama-3.3-70b-versatile"),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> AnalysisJob | None:
        result = await self.db.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_meeting_and_transcript(
        self,
        meeting_id: uuid.UUID,
        transcript_id: uuid.UUID,
    ) -> AnalysisJob | None:
        result = await self.db.execute(
            select(AnalysisJob).where(
                AnalysisJob.meeting_id == meeting_id,
                AnalysisJob.transcript_id == transcript_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, job: AnalysisJob, **kwargs) -> AnalysisJob:
        for key, value in kwargs.items():
            setattr(job, key, value)
        await self.db.commit()
        await self.db.refresh(job)
        return job
