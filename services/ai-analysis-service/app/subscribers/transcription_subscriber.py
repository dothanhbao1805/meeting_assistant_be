import json
import logging
from app.core.redis import redis_client, QUEUE_ANALYSIS

logger = logging.getLogger(__name__)

CHANNEL_TRANSCRIPTION_COMPLETED = (
    "event:transcription.completed"  # khớp với bên transcript service
)


async def start_subscriber():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL_TRANSCRIPTION_COMPLETED)
    logger.info(f"Subscribed to: {CHANNEL_TRANSCRIPTION_COMPLETED}")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue  # bỏ qua confirm message khi subscribe

        try:
            payload = json.loads(message["data"])
            logger.info(f"Nhận event transcription.completed: {payload}")

            # Push vào queue để worker xử lý
            job_message = {
                "meeting_id": payload["meeting_id"],
                "transcript_id": payload["transcript_id"],
            }
            await redis_client.lpush(QUEUE_ANALYSIS, json.dumps(job_message))

        except Exception as e:
            logger.error(f"Subscriber error: {e}")
