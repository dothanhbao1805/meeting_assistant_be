import asyncio
import json
import logging
from datetime import datetime
import uuid
from app.core.redis import redis_client, QUEUE_TRANSCRIPTION
from app.db.database import AsyncSessionLocal
from app.repositories.job_repo import TranscriptionJobRepo
from app.services.deepgram_client import DeepgramClient

logger = logging.getLogger(__name__)


async def process_message(message: dict):
    """
    Xử lý message từ Redis queue

    Flow:
    1. Kiểm tra idempotency (job đã tồn tại?)
    2. Tạo job mới (status=queued)
    3. Gọi Deepgram API với signed URL
    4. Cập nhật job với deepgram_request_id (status=processing)
    5. Nếu lỗi, cập nhật status=failed
    """

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
                "company_id": message.get("company_id"),
                "status": "queued",
                "model": message.get("model", "nova-2"),
                "options": {
                    "diarize": message.get("diarize", True),
                    "punctuate": message.get("punctuate", True),
                    "language": message.get("language_code", "vi"),
                    "smart_format": message.get("smart_format", True),
                },
            }
        )
        logger.info(f"Tạo job thành công: {job.id} — status: queued")

        # Lay signed URL tu message
        signed_url = message.get("signed_url")

        if not signed_url:
            error_msg = "Missing signed_url in message"
            logger.error(error_msg)
            job.status = "failed"
            job.error_message = error_msg
            await db.commit()
            
            from app.services.meeting_service_client import meeting_service_client
            await meeting_service_client.update_meeting_status(str(job.meeting_id), "failed")
            
            return

        # call Deepgram API
        try:
            client = DeepgramClient()
            dg_result = await client.transcribe_url(
                signed_url=signed_url,
                request_id=str(job.id),
                model=job.model or "nova-2",
                options=job.options,
            )

            # Cap nhat job voi deepgram_request_id va status=processing
            job.deepgram_request_id = dg_result["dg_request_id"]
            job.status = "processing"
            job.started_at = datetime.utcnow()
            await db.commit()

            from app.services.meeting_service_client import meeting_service_client
            await meeting_service_client.update_meeting_status(str(job.meeting_id), "transcribing")

            logger.info(
                f"Job {job.id} sent to Deepgram — "
                f"deepgram_request_id: {job.deepgram_request_id}"
            )

        except Exception as e:
            logger.error(f"Error calling Deepgram: {e}", exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()

            from app.services.meeting_service_client import meeting_service_client
            await meeting_service_client.update_meeting_status(str(job.meeting_id), "failed")


async def run_worker():
    """Worker loop — lắng nghe queue và xử lý message"""
    logger.info("Worker started — listening queue: " + QUEUE_TRANSCRIPTION)
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
