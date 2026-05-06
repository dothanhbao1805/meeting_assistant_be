import json
import logging
import uuid

from app.core.config import settings
from app.core.redis import QUEUE_ANALYSIS, redis_client
from app.db.database import AsyncSessionLocal
from app.repositories.job_repo import AnalysisJobRepo

logger = logging.getLogger(__name__)

CHANNEL_TRANSCRIPTION_COMPLETED = "event:transcription.completed"


async def start_subscriber():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL_TRANSCRIPTION_COMPLETED)
    logger.info("Subscribed to: %s", CHANNEL_TRANSCRIPTION_COMPLETED)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            payload = json.loads(message["data"])
            logger.info("Received transcription.completed event: %s", payload)
            meeting_id = uuid.UUID(payload["meeting_id"])
            transcript_id = uuid.UUID(payload["transcript_id"])

            async with AsyncSessionLocal() as db:
                repo = AnalysisJobRepo(db)
                existing = await repo.get_by_meeting_and_transcript(
                    meeting_id=meeting_id,
                    transcript_id=transcript_id,
                )

                if existing:
                    logger.info(
                        "Analysis job already exists for transcript %s: %s",
                        payload["transcript_id"],
                        existing.id,
                    )
                    continue

                job = await repo.create(
                    {
                        "meeting_id": meeting_id,
                        "transcript_id": transcript_id,
                        "model": settings.GROQ_MODEL,
                    }
                )

            job_message = {
                "job_id": str(job.id),
                "meeting_id": payload["meeting_id"],
                "transcript_id": payload["transcript_id"],
            }
            await redis_client.lpush(QUEUE_ANALYSIS, json.dumps(job_message))

        except Exception as e:
            logger.error("Subscriber error: %s", e)
