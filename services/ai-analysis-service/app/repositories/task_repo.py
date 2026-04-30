from app.models.extracted_task import ExtractedTask
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from sqlalchemy import select, update
from app.models.analysis_job import AnalysisJob
from typing import List

class TaskRepo:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_analysis_by_meeting_id(self, meeting_id: uuid.UUID):
        result = await self.db.execute(
            select(AnalysisJob).where(
                AnalysisJob.meeting_id == meeting_id
            )
        )
        return result.scalar_one_or_none()

    async def create_task(self, data:dict,analysis_job_id: uuid.UUID):
        task = ExtractedTask(
            id=uuid.uuid4(),
            meeting_id=data.meeting_id,
            analysis_job_id=analysis_job_id,
            title=data.title,
            description=data.description,
            resolved_user_id=data.resolved_user_id,
            deadline_date=data.deadline_date,
            priority=data.priority,
            status="pending",
            created_at=datetime.utcnow(),
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task
    
    async def get_tasks_by_meeting(self, meeting_id: uuid.UUID):
        result = await self.db.execute(
            select(ExtractedTask).where(
                ExtractedTask.meeting_id == meeting_id
            )
        )
        return result.scalars().all()

    async def confirm_tasks(self, task_ids):
        stmt = (
            update(ExtractedTask)
            .where(ExtractedTask.id.in_(task_ids))
            .values(status="confirmed",
                    confirmed_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
    
    async def get_confirmed_tasks_by_meeting(self, meeting_id: uuid.UUID):
        result = await self.db.execute(
            select(ExtractedTask).where(
                ExtractedTask.meeting_id == meeting_id,
                ExtractedTask.status == "confirmed"
            )
        )
        return result.scalars().all()
    
    async def update_tasks_status(self, task_ids: List[uuid.UUID], new_status: str):
        stmt = (
            update(ExtractedTask)
            .where(ExtractedTask.id.in_(task_ids))
            .values(status=new_status)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
    
        return result.rowcount