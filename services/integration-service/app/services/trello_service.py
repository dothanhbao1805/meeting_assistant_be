import json
import logging
from datetime import datetime, timezone

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_client import get_company_trello_credentials, get_trello_member_id
from app.core.config import settings
from app.core.trello_client import TrelloClient
from app.repositories.trello_sync_repo import TrelloSyncRepo
from app.schemas.trello import ConfirmedTask, TrelloSyncResult

logger = logging.getLogger(__name__)

CHANNEL_TRELLO_SYNCED = "trello.synced"


async def sync_tasks_to_trello(
    db: AsyncSession,
    meeting_id: str,
    company_id: str,
    trello_board_id: str,
    trello_list_id: str,
    confirmed_tasks: list[ConfirmedTask],
) -> dict:
    repo = TrelloSyncRepo(db)
    results: list[TrelloSyncResult] = []

    # 1. Lấy credentials từ Company Service
    creds = await get_company_trello_credentials(company_id)
    trello_api_key = creds.get("trello_api_key")
    trello_token = creds.get("trello_token")

    if not trello_api_key or not trello_token:
        raise ValueError(f"Company {company_id} chưa cấu hình Trello credentials")

    client = TrelloClient(api_key=trello_api_key, token=trello_token)

    # 2. Xử lý từng task
    for task in confirmed_tasks:
        existing_log = await repo.get_by_task_id(task.task_id)
        if existing_log and existing_log.sync_status == "success":
            results.append(
                TrelloSyncResult(
                    task_id=task.task_id,
                    trello_card_id=existing_log.trello_card_id,
                    trello_card_url=existing_log.trello_card_url,
                    status="success",
                )
            )
            logger.info(
                f"[TRELLO] Task {task.task_id} already synced, skipping duplicate"
            )
            continue

        trello_member_id = None
        assigned_trello_user_id = None

        # Lấy trello_member_id nếu có resolved_user_id
        if task.resolved_user_id:
            trello_member_id = await get_trello_member_id(
                company_id, str(task.resolved_user_id)
            )
            assigned_trello_user_id = trello_member_id

        try:
            # 3. Tạo Trello card
            card = await client.create_card(
                list_id=trello_list_id,
                board_id=trello_board_id,
                title=task.title,
                description=task.description,
                due_date=task.deadline_date.isoformat() if task.deadline_date else None,
                member_id=trello_member_id,
                priority=task.priority,
            )

            # 4. Lưu log success
            await repo.create(
                {
                    "task_id": task.task_id,
                    "meeting_id": meeting_id,
                    "company_id": company_id,
                    "trello_board_id": trello_board_id,
                    "trello_list_id": trello_list_id,
                    "trello_card_id": card["id"],
                    "trello_card_url": card["url"],
                    "assigned_trello_user_id": assigned_trello_user_id,
                    "sync_status": "success",
                    "synced_at": datetime.now(timezone.utc),
                }
            )

            results.append(
                TrelloSyncResult(
                    task_id=task.task_id,
                    trello_card_id=card["id"],
                    trello_card_url=card["url"],
                    status="success",
                )
            )
            logger.info(f"[TRELLO] Task {task.task_id} → card {card['id']} ✓")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[TRELLO] Task {task.task_id} FAILED: {error_msg}")

            # Lưu log failed
            await repo.create(
                {
                    "task_id": task.task_id,
                    "meeting_id": meeting_id,
                    "company_id": company_id,
                    "trello_board_id": trello_board_id,
                    "trello_list_id": trello_list_id,
                    "sync_status": "failed",
                    "error_message": error_msg,
                    "synced_at": datetime.now(timezone.utc),
                }
            )

            results.append(
                TrelloSyncResult(
                    task_id=task.task_id,
                    status="failed",
                    error=error_msg,
                )
            )

    synced_count = sum(1 for r in results if r.status == "success")
    failed_count = sum(1 for r in results if r.status == "failed")

    # 5. Publish event trello.synced
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    event_payload = {
        "event": "trello.synced",
        "meeting_id": str(meeting_id),
        "company_id": str(company_id),
        "synced_count": synced_count,
        "failed_count": failed_count,
        "results": [
            {
                "task_id": str(result.task_id),
                "trello_card_id": result.trello_card_id,
                "trello_card_url": result.trello_card_url,
                "status": result.status,
                "error": result.error,
            }
            for result in results
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await redis_client.publish(CHANNEL_TRELLO_SYNCED, json.dumps(event_payload))
    except Exception as e:
        logger.warning(f"[TRELLO] Publish trello.synced thất bại: {e}")
    finally:
        await redis_client.aclose()

    return {
        "synced_count": synced_count,
        "failed_count": failed_count,
        "results": results,
    }
