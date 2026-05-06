import json
import logging
import httpx
from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

CHANNEL_AUTO_RESOLVE_COMPLETED = "event:auto_resolve.completed"


async def start_subscriber():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL_AUTO_RESOLVE_COMPLETED)
    logger.info(f"Subscribed to: {CHANNEL_AUTO_RESOLVE_COMPLETED}")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            payload = json.loads(message["data"])
            if payload.get("event") != "auto_resolve.completed":
                continue

            logger.info(f"Nhận event auto_resolve.completed: {payload}")

            meeting_id = payload["meeting_id"]
            transcript_id = payload["transcript_id"]

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.SELF_BASE_URL}/analysis-jobs/",
                    json={
                        "meeting_id": meeting_id,
                        "transcript_id": transcript_id,
                    },
                )
                if resp.status_code == 409:
                    logger.info(
                        f"Analysis job đã tồn tại cho transcript {transcript_id}, bỏ qua"
                    )
                else:
                    resp.raise_for_status()
                    logger.info(f"Tạo analysis job thành công: {resp.json()}")

        except Exception as e:
            logger.error(f"Subscriber error: {e}", exc_info=True)
