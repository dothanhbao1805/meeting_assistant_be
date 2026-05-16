import json
import uuid
from datetime import datetime, timezone

import httpx
import redis.asyncio as redis
from fastapi import HTTPException

from app.core.config import settings
from app.repositories.task_repo import TaskRepo
from app.schemas.task import CreateTaskRequest, SkippedTask
from difflib import SequenceMatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        await self._publish_confirmed_tasks(meeting_id)

        return {
            "confirmed_count": confirmed_count,
            "skipped_count": 0,
            "skipped_tasks": [],
        }

    async def sync_to_integration(self, meeting_id: uuid.UUID):
        return await self._publish_confirmed_tasks(meeting_id)

    async def _publish_confirmed_tasks(self, meeting_id: uuid.UUID):
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
                    f"{settings.MEETING_SERVICE_URL}/internal/meetings/{meeting_id}",
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

    def extract_word_corrections(self, old_text: str, new_text: str) -> list[dict]:
        old_words = old_text.lower().split()
        new_words = new_text.lower().split()
        corrections = []
        matcher = SequenceMatcher(None, old_words, new_words)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                wrong = " ".join(old_words[i1:i2])
                correct = " ".join(new_words[j1:j2])
                if wrong and correct:
                    corrections.append({"wrong_text": wrong, "correct_text": correct})
        return corrections

    async def save_corrections_to_company(
        self, company_id: str, corrections: list[dict]
    ):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                url = f"{settings.COMPANY_SERVICE_URL}/internal/corrections"
                resp = await client.post(
                    url, json={"company_id": company_id, "corrections": corrections}
                )
                resp.raise_for_status()
                logger.info(f"[corrections] Response: {resp.status_code}")
        except Exception as e:
            logger.warning(f"[corrections] Lỗi: {e}")

    async def update_task(self, task_id: uuid.UUID, data: dict):
        old_task = await self.repo.get_task_by_id(task_id)
        if not old_task:
            raise HTTPException(status_code=404, detail="Task not found")

        old_title = old_task.title
        old_description = old_task.description or ""

        job = await self.repo.get_analysis_job_by_id(old_task.analysis_job_id)
        company_id = str(job.company_id) if job and job.company_id else None

        task = await self.repo.update_task(task_id, data)

        if company_id:
            corrections = []

            if "title" in data and data["title"] != old_title:
                for c in self.extract_word_corrections(old_title, data["title"]):
                    c["context"] = old_title  # thêm context
                    corrections.append(c)

            if "description" in data and data["description"] != old_description:
                for c in self.extract_word_corrections(
                    old_description, data["description"] or ""
                ):
                    c["context"] = old_description  # thêm context
                    corrections.append(c)

            if corrections:
                await self.save_corrections_to_company(company_id, corrections)
                logger.info(f"Saved {len(corrections)} corrections: {corrections}")

        return task
