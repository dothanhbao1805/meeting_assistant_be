import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent


class CalendarEventRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> CalendarEvent:
        event = CalendarEvent(
            id=uuid.uuid4(),
            task_id=data["task_id"],
            meeting_id=data["meeting_id"],
            company_id=data.get("company_id"),
            user_id=data.get("user_id"),
            google_calendar_id=data.get("google_calendar_id"),
            google_event_id=data.get("google_event_id"),
            event_link=data.get("event_link"),
            title=data["title"],
            due_date=data.get("due_date"),
            sync_status=data.get("sync_status", "pending"),
            error_message=data.get("error_message"),
            retries=data.get("retries", 0),
            synced_at=data.get("synced_at"),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_by_task_id(self, task_id: uuid.UUID) -> CalendarEvent | None:
        result = await self.db.execute(
            select(CalendarEvent).where(CalendarEvent.task_id == task_id)
        )
        return result.scalar_one_or_none()
