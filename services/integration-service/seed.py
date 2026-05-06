import asyncio
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import delete

from app.db.database import AsyncSessionLocal
from app.models.calendar_event import CalendarEvent
from app.models.sync_queue import SyncQueue
from app.models.trello_sync_log import TrelloSyncLog


MEETING_DONE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
MEETING_PROCESSING_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
COMPANY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


async def reset_sample_data(db):
    meeting_ids = [MEETING_DONE_ID, MEETING_PROCESSING_ID]

    await db.execute(delete(TrelloSyncLog).where(TrelloSyncLog.meeting_id.in_(meeting_ids)))
    await db.execute(delete(CalendarEvent).where(CalendarEvent.meeting_id.in_(meeting_ids)))
    await db.execute(delete(SyncQueue).where(SyncQueue.meeting_id.in_(meeting_ids)))
    await db.commit()


async def seed_done_meeting(db):
    now = datetime.now(timezone.utc)
    task_1 = uuid.UUID("33333333-3333-3333-3333-333333333331")
    task_2 = uuid.UUID("33333333-3333-3333-3333-333333333332")

    db.add_all(
        [
            SyncQueue(
                id=uuid.UUID("44444444-4444-4444-4444-444444444441"),
                meeting_id=MEETING_DONE_ID,
                job_type="trello",
                payload={"task_count": 2, "source": "seed"},
                status="done",
                scheduled_at=now,
                processed_at=now,
                attempts=1,
                max_attempts=3,
            ),
            SyncQueue(
                id=uuid.UUID("44444444-4444-4444-4444-444444444442"),
                meeting_id=MEETING_DONE_ID,
                job_type="calendar",
                payload={"task_count": 1, "source": "seed"},
                status="done",
                scheduled_at=now,
                processed_at=now,
                attempts=1,
                max_attempts=3,
            ),
            TrelloSyncLog(
                id=uuid.UUID("55555555-5555-5555-5555-555555555551"),
                task_id=task_1,
                meeting_id=MEETING_DONE_ID,
                company_id=COMPANY_ID,
                trello_board_id="board_seed",
                trello_list_id="list_seed",
                trello_card_id="card_seed_1",
                trello_card_url="https://trello.com/c/card_seed_1",
                sync_status="success",
                retries=0,
                synced_at=now,
                created_at=now,
            ),
            TrelloSyncLog(
                id=uuid.UUID("55555555-5555-5555-5555-555555555552"),
                task_id=task_2,
                meeting_id=MEETING_DONE_ID,
                company_id=COMPANY_ID,
                trello_board_id="board_seed",
                trello_list_id="list_seed",
                trello_card_id="card_seed_2",
                trello_card_url="https://trello.com/c/card_seed_2",
                sync_status="success",
                retries=0,
                synced_at=now,
                created_at=now,
            ),
            CalendarEvent(
                id=uuid.UUID("66666666-6666-6666-6666-666666666661"),
                task_id=task_1,
                meeting_id=MEETING_DONE_ID,
                user_id=USER_ID,
                google_calendar_id="primary",
                google_event_id="event_seed_1",
                event_link="https://calendar.google.com/calendar/event?eid=event_seed_1",
                title="Send sprint summary",
                due_date=date(2026, 5, 5),
                sync_status="success",
                synced_at=now,
            ),
        ]
    )


async def seed_processing_meeting(db):
    now = datetime.now(timezone.utc)
    task_1 = uuid.UUID("77777777-7777-7777-7777-777777777771")
    task_2 = uuid.UUID("77777777-7777-7777-7777-777777777772")

    db.add_all(
        [
            SyncQueue(
                id=uuid.UUID("88888888-8888-8888-8888-888888888881"),
                meeting_id=MEETING_PROCESSING_ID,
                job_type="trello",
                payload={"task_count": 2, "source": "seed"},
                status="processing",
                scheduled_at=now,
                processed_at=None,
                attempts=1,
                max_attempts=3,
            ),
            SyncQueue(
                id=uuid.UUID("88888888-8888-8888-8888-888888888882"),
                meeting_id=MEETING_PROCESSING_ID,
                job_type="calendar",
                payload={"task_count": 1, "source": "seed"},
                status="failed",
                scheduled_at=now,
                processed_at=now,
                attempts=3,
                max_attempts=3,
            ),
            TrelloSyncLog(
                id=uuid.UUID("99999999-9999-9999-9999-999999999991"),
                task_id=task_1,
                meeting_id=MEETING_PROCESSING_ID,
                company_id=COMPANY_ID,
                trello_board_id="board_seed",
                trello_list_id="list_seed",
                trello_card_id="card_seed_processing_1",
                trello_card_url="https://trello.com/c/card_seed_processing_1",
                sync_status="success",
                retries=0,
                synced_at=now,
                created_at=now,
            ),
            TrelloSyncLog(
                id=uuid.UUID("99999999-9999-9999-9999-999999999992"),
                task_id=task_2,
                meeting_id=MEETING_PROCESSING_ID,
                company_id=COMPANY_ID,
                trello_board_id="board_seed",
                trello_list_id="list_seed",
                sync_status="failed",
                error_message="Seed sample Trello failure",
                retries=3,
                synced_at=now,
                created_at=now,
            ),
            CalendarEvent(
                id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
                task_id=task_2,
                meeting_id=MEETING_PROCESSING_ID,
                user_id=USER_ID,
                google_calendar_id="primary",
                title="Follow up failed calendar sync",
                due_date=date(2026, 5, 6),
                sync_status="failed",
                synced_at=now,
            ),
        ]
    )


async def seed():
    async with AsyncSessionLocal() as db:
        await reset_sample_data(db)
        await seed_done_meeting(db)
        await seed_processing_meeting(db)
        await db.commit()

    print("Seeded integration-service sample data")
    print(f"done meeting_id       : {MEETING_DONE_ID}")
    print(f"processing meeting_id : {MEETING_PROCESSING_ID}")


if __name__ == "__main__":
    asyncio.run(seed())
