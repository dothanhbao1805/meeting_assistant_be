from asyncio import tasks
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.extracted_task import ExtractedTask
from app.models.analysis_job import AnalysisJob


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
                resolved_user_id=t.get("resolved_user_id"),  # thêm
                deadline_raw=t.get("deadline_raw"),
                deadline_date=t.get("deadline_date"),          # thêm
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

    async def create_task(
        self, data: dict, analysis_job_id: uuid.UUID
    ) -> ExtractedTask:
        task = ExtractedTask(
            id=uuid.uuid4(),
            meeting_id=data["meeting_id"],
            analysis_job_id=analysis_job_id,
            title=data["title"],
            description=data.get("description"),
            raw_assignee_text=data.get("raw_assignee_text"),
            resolved_user_id=data.get("resolved_user_id"),
            deadline_raw=data.get("deadline_raw"),
            deadline_date=data.get("deadline_date"),
            priority=data.get("priority", "medium"),
            status="pending",
            ai_confidence=data.get("ai_confidence"),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_tasks_by_meeting(self, meeting_id: uuid.UUID) -> list[ExtractedTask]:
        result = await self.db.execute(
            select(ExtractedTask).where(ExtractedTask.meeting_id == meeting_id)
        )
        return result.scalars().all()

    async def get_confirmed_tasks_by_meeting(
        self, meeting_id: uuid.UUID
    ) -> list[ExtractedTask]:
        result = await self.db.execute(
            select(ExtractedTask).where(
                ExtractedTask.meeting_id == meeting_id,
                ExtractedTask.status == "confirmed",
            )
        )
        return result.scalars().all()

    async def get_analysis_by_meeting_id(
        self, meeting_id: uuid.UUID
    ) -> AnalysisJob | None:
        result = await self.db.execute(
            select(AnalysisJob).where(AnalysisJob.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def confirm_tasks(self, task_ids: List[uuid.UUID]) -> int:
        stmt = (
            update(ExtractedTask)
            .where(ExtractedTask.id.in_(task_ids))
            .values(
                status="confirmed",
                confirmed_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def update_tasks_status(
        self, task_ids: List[uuid.UUID], new_status: str
    ) -> int:
        stmt = (
            update(ExtractedTask)
            .where(ExtractedTask.id.in_(task_ids))
            .values(status=new_status)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def update_task(self, task_id: uuid.UUID, data: dict) -> ExtractedTask | None:
        stmt = (
            update(ExtractedTask)
            .where(ExtractedTask.id == task_id)
            .values(**data)
            .returning(ExtractedTask)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()


TaskRepo = ExtractedTaskRepo
