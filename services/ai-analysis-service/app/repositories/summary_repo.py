from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
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
