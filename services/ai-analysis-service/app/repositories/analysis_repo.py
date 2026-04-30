import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.analysis_job import AnalysisJob
from app.models.meeting_summary import MeetingSummary
from app.models.extracted_task import ExtractedTask


class MeetingAnalysisRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_job_with_results(
        self, meeting_id: uuid.UUID
    ) -> AnalysisJob | None:
        """Lấy analysis job mới nhất của meeting, kèm summary và tasks."""
        result = await self.db.execute(
            select(AnalysisJob)
            .where(AnalysisJob.meeting_id == meeting_id)
            .options(
                selectinload(AnalysisJob.summary),
                selectinload(AnalysisJob.tasks),
            )
            .order_by(AnalysisJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_unresolved_speakers(self, meeting_id: uuid.UUID) -> list[str]:
        """
        Lấy danh sách speaker_label chưa được resolve (resolved_user_id IS NULL)
        từ extracted_tasks của meeting.
        """
        result = await self.db.execute(
            select(ExtractedTask.raw_assignee_text)
            .where(
                ExtractedTask.meeting_id == meeting_id,
                ExtractedTask.resolved_user_id == None,
                ExtractedTask.raw_assignee_text != None,
            )
            .distinct()
        )
        return [row[0] for row in result.fetchall()]
