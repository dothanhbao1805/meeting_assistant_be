import json
import logging
from datetime import datetime, timezone

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_client import (
    get_company_google_credentials,
    get_member_google_email,
)
from app.core.config import settings
from app.core.google_calendar_client import GoogleCalendarClient
from app.repositories.calendar_event_repo import CalendarEventRepo
from app.schemas.calendar import CalendarSyncResult
from app.schemas.trello import ConfirmedTask

logger = logging.getLogger(__name__)

CHANNEL_CALENDAR_SYNCED = "calendar.synced"


async def sync_tasks_to_google_calendar(
    db: AsyncSession,
    meeting_id: str,
    company_id: str,
    confirmed_tasks: list[ConfirmedTask],
) -> dict:
    repo = CalendarEventRepo(db)
    results: list[CalendarSyncResult] = []

    creds = await get_company_google_credentials(company_id)
    access_token = creds.get("google_access_token")
    calendar_id = creds.get("google_calendar_id")

    if not access_token or not calendar_id:
        raise ValueError(f"Company {company_id} chưa cấu hình Google Calendar")

    client = GoogleCalendarClient(access_token=access_token)

    for task in confirmed_tasks:
        existing_event = await repo.get_by_task_id(task.task_id)
        if existing_event and existing_event.sync_status == "success":
            results.append(
                CalendarSyncResult(
                    task_id=task.task_id,
                    google_event_id=existing_event.google_event_id,
                    event_link=existing_event.event_link,
                    status="success",
                )
            )
            logger.info(
                f"[CALENDAR] Task {task.task_id} already synced, skipping duplicate"
            )
            continue

        if not task.deadline_date:
            error_msg = "Task has no deadline_date"
            await repo.create(
                {
                    "task_id": task.task_id,
                    "meeting_id": meeting_id,
                    "company_id": company_id,
                    "user_id": task.resolved_user_id,
                    "google_calendar_id": calendar_id,
                    "title": task.title,
                    "due_date": None,
                    "sync_status": "failed",
                    "error_message": error_msg,
                    "synced_at": datetime.now(timezone.utc),
                }
            )
            results.append(
                CalendarSyncResult(
                    task_id=task.task_id,
                    status="failed",
                    error=error_msg,
                )
            )
            continue

        attendee_email = None
        if task.resolved_user_id:
            attendee_email = await get_member_google_email(
                company_id, str(task.resolved_user_id)
            )

        description_parts = []
        if task.description:
            description_parts.append(task.description)
        if task.priority:
            description_parts.append(f"Priority: {task.priority}")
        description_parts.append("Created by MeetingAI")

        try:
            event = await client.create_all_day_event(
                calendar_id=calendar_id,
                title=task.title,
                description="\n\n".join(description_parts),
                due_date=task.deadline_date,
                attendee_email=attendee_email,
            )

            await repo.create(
                {
                    "task_id": task.task_id,
                    "meeting_id": meeting_id,
                    "company_id": company_id,
                    "user_id": task.resolved_user_id,
                    "google_calendar_id": calendar_id,
                    "google_event_id": event.get("id"),
                    "event_link": event.get("htmlLink"),
                    "title": task.title,
                    "due_date": task.deadline_date,
                    "sync_status": "success",
                    "synced_at": datetime.now(timezone.utc),
                }
            )

            results.append(
                CalendarSyncResult(
                    task_id=task.task_id,
                    google_event_id=event.get("id"),
                    event_link=event.get("htmlLink"),
                    status="success",
                )
            )
            logger.info(f"[CALENDAR] Task {task.task_id} → event {event.get('id')} ✓")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[CALENDAR] Task {task.task_id} FAILED: {error_msg}")
            await repo.create(
                {
                    "task_id": task.task_id,
                    "meeting_id": meeting_id,
                    "company_id": company_id,
                    "user_id": task.resolved_user_id,
                    "google_calendar_id": calendar_id,
                    "title": task.title,
                    "due_date": task.deadline_date,
                    "sync_status": "failed",
                    "error_message": error_msg,
                    "synced_at": datetime.now(timezone.utc),
                }
            )
            results.append(
                CalendarSyncResult(
                    task_id=task.task_id,
                    status="failed",
                    error=error_msg,
                )
            )

    synced_count = sum(1 for r in results if r.status == "success")
    failed_count = sum(1 for r in results if r.status == "failed")

    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    event_payload = {
        "event": "calendar.synced",
        "meeting_id": str(meeting_id),
        "company_id": str(company_id),
        "synced_count": synced_count,
        "failed_count": failed_count,
        "results": [
            {
                "task_id": str(result.task_id),
                "google_event_id": result.google_event_id,
                "event_link": result.event_link,
                "status": result.status,
                "error": result.error,
            }
            for result in results
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await redis_client.publish(CHANNEL_CALENDAR_SYNCED, json.dumps(event_payload))
    except Exception as e:
        logger.warning(f"[CALENDAR] Publish calendar.synced thất bại: {e}")
    finally:
        await redis_client.aclose()

    return {
        "synced_count": synced_count,
        "failed_count": failed_count,
        "results": results,
    }
