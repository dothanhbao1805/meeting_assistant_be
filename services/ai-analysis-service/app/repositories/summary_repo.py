import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.meeting_summary import MeetingSummary


class MeetingSummaryRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> MeetingSummary:
        summary = MeetingSummary(
            analysis_job_id=data["analysis_job_id"],
            meeting_id=data["meeting_id"],
            summary_text=data.get("summary_text"),
            key_decisions=data.get("key_decisions", []),
            attendees_mentioned=data.get("attendees_mentioned", []),
            topics_covered=data.get("topics_covered", []),
            language=data.get("language", "vi"),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)
        return summary

    async def get_by_meeting_id(self, meeting_id: uuid.UUID) -> MeetingSummary | None:
        result = await self.db.execute(
            select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, summary_id: uuid.UUID) -> MeetingSummary | None:
        result = await self.db.execute(
            select(MeetingSummary).where(MeetingSummary.id == summary_id)
        )
        return result.scalar_one_or_none()

    async def update(self, summary_id: uuid.UUID, data: dict) -> MeetingSummary | None:
        stmt = (
            update(MeetingSummary)
            .where(MeetingSummary.id == summary_id)
            .values(**data)
            .returning(MeetingSummary)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()
