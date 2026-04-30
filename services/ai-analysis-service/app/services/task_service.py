from app.schemas.task import CreateTaskRequest
from app.schemas.task import SkippedTask
from app.repositories.task_repo import TaskRepo
from fastapi import HTTPException
import redis.asyncio as redis
import json
from app.core.config import settings
import uuid

class TaskService:
    def __init__(self, repo: TaskRepo):
        self.repo = repo
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def create_task(self, data: CreateTaskRequest):
        job = await self.repo.get_analysis_by_meeting_id(data.meeting_id)

        if not job:
            raise HTTPException(status_code=404, detail="Analysis job not found")

        return await self.repo.create_task(
            data,
            analysis_job_id=job.id
        )
    
    async def confirm_all_tasks(self, meeting_id):
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
                skipped.append(
                    SkippedTask(
                        task_id=t.id,
                        missing_fields=missing
                    )
                )
            else:
                valid_task_ids.append(t.id)

        # IMPORTANT: nếu có 1 task lỗi → không confirm cái nào
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
        # 1. Gọi Repo lấy tasks (Repo đã có sẵn DB bên trong)
        tasks = await self.repo.get_confirmed_tasks_by_meeting(meeting_id)
        
        if not tasks:
            return {"status": "skipped", "message": "No confirmed tasks"}

        task_ids = [t.id for t in tasks]
        
        # 2. Map dữ liệu sang JSON
        task_data = [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "resolved_user_id": str(t.resolved_user_id)
            } for t in tasks
        ]

        # 3. Payload gửi sang Integration Service qua Redis
        payload = {
            "meeting_id": str(meeting_id),
            "tasks": json.dumps(task_data)
        }

        try:
            # 4. Đẩy vào Redis Stream
            await self.redis_client.xadd("integration:sync_stream", payload)

            # 5. Cập nhật trạng thái syncing
            await self.repo.update_tasks_status(task_ids, "syncing")

            return {"status": "success", "synced_count": len(task_ids)}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Redis Error: {str(e)}")
        
        
    