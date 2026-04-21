import asyncio
import json
import logging
import uuid
from app.core.redis import redis_client, QUEUE_TRANSCRIPTION
from app.db.database import AsyncSessionLocal
from app.repositories.job_repo import TranscriptionJobRepo

logger = logging.getLogger(__name__)


async def process_message(message: dict):
    async with AsyncSessionLocal() as db:
        repo = TranscriptionJobRepo(db)

        # Nếu có job_id → đây là retry, không tạo job mới
        if message.get("job_id"):
            job = await repo.get_by_id(uuid.UUID(message["job_id"]))
            if not job:
                logger.error(f"Retry job không tồn tại: {message['job_id']}")
                return
            logger.info(f"Retry job: {job.id} — status: {job.status}")
            # TODO: gọi Deepgram ở đây
            return

        # Không có job_id → đây là job mới, check idempotency
        existing = await repo.get_by_meeting_and_file(
            meeting_id=message["meeting_id"],
            media_file_id=message["media_file_id"],
        )
        if existing:
            logger.info(f"Job đã tồn tại: {existing.id}, bỏ qua")
            return

        # Tạo job mới
        job = await repo.create(
            {
                "meeting_id": message["meeting_id"],
                "media_file_id": message["media_file_id"],
                "status": "queued",
                "model": "nova-2",
                "options": {
                    "diarize": True,
                    "punctuate": True,
                    "language": message.get("language_code", "vi"),
                },
            }
        )
        logger.info(f"Tạo job thành công: {job.id} — status: queued")
        # TODO: gọi Deepgram ở đây


async def run_worker():
    logger.info("Worker started — listening: " + QUEUE_TRANSCRIPTION)
    while True:
        try:
            result = await redis_client.brpop(QUEUE_TRANSCRIPTION, timeout=5)
            if result:
                _, raw = result
                message = json.loads(raw)
                logger.info(f"Nhận message: {message}")
                await process_message(message)
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run_worker())
