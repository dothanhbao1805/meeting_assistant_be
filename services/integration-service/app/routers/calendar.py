import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.calendar import CalendarSyncRequest, CalendarSyncResponse
from app.services.calendar_service import sync_tasks_to_google_calendar

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["Google Calendar"])


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendar(
    payload: CalendarSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await sync_tasks_to_google_calendar(
        db=db,
        meeting_id=str(payload.meeting_id),
        company_id=str(payload.company_id),
        confirmed_tasks=payload.confirmed_tasks,
    )
    return CalendarSyncResponse(**result)
