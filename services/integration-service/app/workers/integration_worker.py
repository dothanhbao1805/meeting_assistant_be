import asyncio
import json
import logging

import httpx

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

CHANNEL_TASKS_CONFIRMED = "tasks.confirmed"


async def handle_tasks_confirmed(payload: dict):
    """Forward payload sang sync endpoints."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"http://localhost:{settings.SERVICE_PORT}/api/v1/trello/sync",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"[WORKER] trello/sync OK: {resp.json()}")
        except Exception as e:
            logger.error(f"[WORKER] trello/sync FAILED: {e}")

        try:
            resp = await client.post(
                f"http://localhost:{settings.SERVICE_PORT}/api/v1/calendar/sync",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"[WORKER] calendar/sync OK: {resp.json()}")
        except Exception as e:
            logger.error(f"[WORKER] calendar/sync FAILED: {e}")


async def run_worker():
    logger.info(
        f"[WORKER] Integration Worker started — listening: {CHANNEL_TASKS_CONFIRMED}"
    )
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL_TASKS_CONFIRMED)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            payload = json.loads(message["data"])
            logger.info(
                f"[WORKER] Nhận event tasks.confirmed: meeting_id={payload.get('meeting_id')}"
            )
            await handle_tasks_confirmed(payload)
        except Exception as e:
            logger.error(f"[WORKER] Lỗi xử lý message: {e}", exc_info=True)
