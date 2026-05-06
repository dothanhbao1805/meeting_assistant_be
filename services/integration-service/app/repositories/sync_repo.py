from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.sync_queue import SyncQueue
from app.models.trello_sync_log import TrelloSyncLog


class SyncRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_queue(
        self,
        meeting_id: UUID | None = None,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SyncQueue], int]:
        query = select(SyncQueue).order_by(
            SyncQueue.scheduled_at.desc().nullslast(),
            SyncQueue.id.desc(),
        )
        count_query = select(func.count()).select_from(SyncQueue)

        filters = []
        if meeting_id is not None:
            filters.append(SyncQueue.meeting_id == meeting_id)
        if status is not None:
            filters.append(SyncQueue.status == status)
        if job_type is not None:
            filters.append(SyncQueue.job_type == job_type)

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.limit(limit).offset(offset))
        return result.scalars().all(), total or 0

    async def list_queue_by_meeting(self, meeting_id: UUID) -> list[SyncQueue]:
        result = await self.db.execute(
            select(SyncQueue).where(SyncQueue.meeting_id == meeting_id)
        )
        return result.scalars().all()

    async def count_trello_by_status(self, meeting_id: UUID) -> dict[str, int]:
        return await self._count_by_status(TrelloSyncLog, meeting_id)

    async def count_calendar_by_status(self, meeting_id: UUID) -> dict[str, int]:
        return await self._count_by_status(CalendarEvent, meeting_id)

    async def _count_by_status(self, model, meeting_id: UUID) -> dict[str, int]:
        result = await self.db.execute(
            select(model.sync_status, func.count())
            .where(model.meeting_id == meeting_id)
            .group_by(model.sync_status)
        )
        return {status: count for status, count in result.all()}
