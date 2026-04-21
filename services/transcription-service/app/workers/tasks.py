import asyncio
import uuid

from app.workers.celery_app import celery
from app.workers.worker_handler import handle_job
from app.db.database import AsyncSessionLocal
from app.repositories.job_repo import TranscriptionJobRepo


async def _mark_failed_async(job_id: str, error: str):
    async with AsyncSessionLocal() as db:
        repo = TranscriptionJobRepo(db)
        await repo.update_status(uuid.UUID(job_id), "failed", error_message=error)


@celery.task(bind=True, max_retries=3, name="process_transcription")
def process_transcription(self, job_id: str):
    try:
        result = handle_job(job_id)
        return result

    except Exception as e:
        print(f"[ERROR] job={job_id} err={e}")

        countdown = 10 * (2 ** self.request.retries)

        try:
            raise self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            print(f"[CRITICAL] Max retries exceeded for job {job_id}")
            asyncio.run(_mark_failed_async(job_id, str(e)))
            raise e