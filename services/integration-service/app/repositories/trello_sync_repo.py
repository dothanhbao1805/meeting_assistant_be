import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.trello_sync_log import TrelloSyncLog


class TrelloSyncRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> TrelloSyncLog:
        log = TrelloSyncLog(
            id=uuid.uuid4(),
            task_id=data["task_id"],
            meeting_id=data["meeting_id"],
            company_id=data["company_id"],
            trello_board_id=data.get("trello_board_id"),
            trello_list_id=data.get("trello_list_id"),
            trello_card_id=data.get("trello_card_id"),
            trello_card_url=data.get("trello_card_url"),
            assigned_trello_user_id=data.get("assigned_trello_user_id"),
            sync_status=data.get("sync_status", "pending"),
            error_message=data.get("error_message"),
            synced_at=data.get("synced_at"),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_by_task_id(self, task_id: uuid.UUID) -> TrelloSyncLog | None:
        result = await self.db.execute(
            select(TrelloSyncLog).where(TrelloSyncLog.task_id == task_id)
        )
        return result.scalar_one_or_none()
