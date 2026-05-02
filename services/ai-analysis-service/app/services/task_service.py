import json
import uuid
from datetime import datetime, timezone

import httpx
import redis.asyncio as redis
from fastapi import HTTPException

from app.core.config import settings
from app.repositories.task_repo import TaskRepo
from app.schemas.task import CreateTaskRequest, SkippedTask

CHANNEL_TASKS_CONFIRMED = "tasks.confirmed"


class TaskService:
    def __init__(self, repo: TaskRepo):
        self.repo = repo
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def create_task(self, data: CreateTaskRequest):
        job = await self.repo.get_analysis_by_meeting_id(data.meeting_id)
        if not job:
            raise HTTPException(status_code=404, detail="Analysis job not found")
        return await self.repo.create_task(data, analysis_job_id=job.id)

    async def update_task(self, task_id: uuid.UUID, data: dict):
        task = await self.repo.update_task(task_id, data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    async def confirm_all_tasks(self, meeting_id: uuid.UUID):
        tasks = await self.repo.get_tasks_by_meeting(meeting_id)

        skipped = []
        valid_task_ids = []

        for t in tasks:
            missing = []
            if not t.resolved_user_id:
                missing.append("resolved_user_id")
            if not t.deadline_date:
                missing.append("deadline_date")

            if missing:
                skipped.append(SkippedTask(task_id=t.id, missing_fields=missing))
            else:
                valid_task_ids.append(t.id)

        if skipped:
            return {
                "confirmed_count": 0,
                "skipped_count": len(skipped),
                "skipped_tasks": skipped,
            }

        confirmed_count = await self.repo.confirm_tasks(valid_task_ids)

        return {
            "confirmed_count": confirmed_count,
            "skipped_count": 0,
            "skipped_tasks": [],
        }

    async def sync_to_integration(self, meeting_id: uuid.UUID):
        # 1. Lấy confirmed tasks
        tasks = await self.repo.get_confirmed_tasks_by_meeting(meeting_id)
        if not tasks:
            return {
                "status": "skipped",
                "message": "No confirmed tasks",
                "synced_count": 0,
            }

        # 2. Gọi Meeting Service lấy trello_board_id, trello_list_id, company_id
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{settings.MEETING_SERVICE_URL}/meetings/{meeting_id}",
                    timeout=10,
                )
                resp.raise_for_status()
                meeting = resp.json()
            except Exception as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Không thể lấy thông tin meeting: {e}",
                )

        # 3. Build payload
        event_payload = {
            "event": "tasks.confirmed",
            "meeting_id": str(meeting_id),
            "company_id": str(meeting.get("company_id"))
            if meeting.get("company_id")
            else None,
            "trello_board_id": meeting.get("trello_board_id"),
            "trello_list_id": meeting.get("trello_list_id"),
            "confirmed_tasks": [
                {
                    "task_id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "resolved_user_id": str(t.resolved_user_id)
                    if t.resolved_user_id
                    else None,
                    "deadline_date": t.deadline_date.isoformat()
                    if t.deadline_date
                    else None,
                    "priority": t.priority,
                }
                for t in tasks
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # 4. Publish lên Redis channel
            await self.redis_client.publish(
                CHANNEL_TASKS_CONFIRMED,
                json.dumps(event_payload),
            )

            # 5. Cập nhật status → syncing
            task_ids = [t.id for t in tasks]
            await self.repo.update_tasks_status(task_ids, "syncing")

            return {"status": "success", "synced_count": len(task_ids)}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Redis error: {e}")
