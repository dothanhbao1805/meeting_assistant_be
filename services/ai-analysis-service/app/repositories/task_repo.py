from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.extracted_task import ExtractedTask


class ExtractedTaskRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, tasks: list[dict]) -> list[ExtractedTask]:
        objects = [
            ExtractedTask(
                analysis_job_id=t["analysis_job_id"],
                meeting_id=t["meeting_id"],
                title=t["title"],
                description=t.get("description"),
                raw_assignee_text=t.get("raw_assignee_text"),
                deadline_raw=t.get("deadline_raw"),
                priority=t.get("priority", "medium"),
                status="pending",
                ai_confidence=t.get("ai_confidence"),
                created_at=datetime.now(timezone.utc),
            )
            for t in tasks
        ]
        self.db.add_all(objects)
        await self.db.commit()
        return objects
