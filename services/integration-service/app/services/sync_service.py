from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_queue import SyncQueue
from app.repositories.sync_repo import SyncRepo


def _serialize_sync_queue_item(item: SyncQueue) -> dict:
    return {
        "id": item.id,
        "meeting_id": item.meeting_id,
        "job_type": item.job_type,
        "payload": item.payload,
        "status": item.status,
        "scheduled_at": item.scheduled_at,
        "processed_at": item.processed_at,
        "attempts": item.attempts,
        "max_attempts": item.max_attempts,
    }


async def get_sync_queue(
    db: AsyncSession,
    meeting_id: UUID | None = None,
    status: str | None = None,
    job_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    repo = SyncRepo(db)
    items, total = await repo.list_queue(
        meeting_id=meeting_id,
        status=status,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_serialize_sync_queue_item(item) for item in items],
    }


async def get_sync_status(db: AsyncSession, meeting_id: UUID) -> dict:
    repo = SyncRepo(db)

    queue_items = await repo.list_queue_by_meeting(meeting_id)
    trello_counts = await repo.count_trello_by_status(meeting_id)
    calendar_counts = await repo.count_calendar_by_status(meeting_id)

    queue_counts: dict[str, int] = {}
    for item in queue_items:
        queue_counts[item.status] = queue_counts.get(item.status, 0) + 1

    failed_count = (
        queue_counts.get("failed", 0)
        + trello_counts.get("failed", 0)
        + calendar_counts.get("failed", 0)
    )
    pending_count = queue_counts.get("pending", 0) + queue_counts.get("processing", 0)

    if failed_count:
        overall_status = "failed"
    elif pending_count:
        overall_status = "processing"
    elif queue_items or trello_counts or calendar_counts:
        overall_status = "done"
    else:
        overall_status = "not_found"

    return {
        "meeting_id": meeting_id,
        "overall_status": overall_status,
        "queue": {
            "total": len(queue_items),
            "by_status": queue_counts,
            "items": [_serialize_sync_queue_item(item) for item in queue_items],
        },
        "trello": {
            "total": sum(trello_counts.values()),
            "by_status": trello_counts,
        },
        "calendar": {
            "total": sum(calendar_counts.values()),
            "by_status": calendar_counts,
        },
    }
