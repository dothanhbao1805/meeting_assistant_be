# app/workers/auto_resolve_worker.py

import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

from app.core.redis import redis_client
from app.db.database import AsyncSessionLocal
from app.services.auto_resolve_service import auto_resolve_speakers

CHANNEL_TRANSCRIPTION_COMPLETED = "event:transcription.completed"
CHANNEL_AUTO_RESOLVE_COMPLETED = "event:auto_resolve.completed"

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    logger.info(
        f"[auto_resolve_worker] Started — subscribing to: {CHANNEL_TRANSCRIPTION_COMPLETED}"
    )

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL_TRANSCRIPTION_COMPLETED)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            event = json.loads(message["data"])
            if event.get("event") != "transcription.completed":
                logger.debug(
                    f"[auto_resolve_worker] Skipping event: {event.get('event')}"
                )
                continue

            await handle_transcription_completed(event)

        except Exception as e:
            logger.error(
                f"[auto_resolve_worker] Error handling message: {e}", exc_info=True
            )


async def handle_transcription_completed(event: dict) -> None:
    transcript_id = UUID(event["transcript_id"])
    meeting_id = event["meeting_id"]
    company_id = event["company_id"]
    meeting_file_id = event.get("meeting_file_id")

    logger.info(f"[auto_resolve_worker] Starting for transcript={transcript_id}")

    async with AsyncSessionLocal() as db:
        try:
            result = await auto_resolve_speakers(
                db=db,
                transcript_id=transcript_id,
                meeting_id=meeting_id,
                company_id=company_id,
                meeting_file_id=meeting_file_id,
                token="",
            )
            logger.info(f"[auto_resolve_worker] Done: {result}")

            # ← THÊM: publish event sau khi xong
            await redis_client.publish(
                CHANNEL_AUTO_RESOLVE_COMPLETED,
                json.dumps(
                    {
                        "event": "auto_resolve.completed",
                        "transcript_id": str(transcript_id),
                        "meeting_id": meeting_id,
                        "company_id": company_id,
                        "meeting_file_id": meeting_file_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
            )
            logger.info(
                f"[auto_resolve_worker] Published auto_resolve.completed for transcript={transcript_id}"
            )

        except Exception as e:
            logger.error(
                f"[auto_resolve_worker] Failed for transcript={transcript_id}: {e}",
                exc_info=True,
            )
            # Vẫn publish để ai-analyst không bị treo mãi, dù resolve thất bại
            await redis_client.publish(
                CHANNEL_AUTO_RESOLVE_COMPLETED,
                json.dumps(
                    {
                        "event": "auto_resolve.completed",
                        "transcript_id": str(transcript_id),
                        "meeting_id": meeting_id,
                        "company_id": company_id,
                        "meeting_file_id": meeting_file_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
            )


if __name__ == "__main__":
    asyncio.run(run_worker())
