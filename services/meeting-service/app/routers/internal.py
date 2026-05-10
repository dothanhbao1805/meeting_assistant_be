import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_meeting_db
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/internal/meetings", tags=["internal"])


@router.get("/{meeting_id}")
async def get_meeting_internal(
    meeting_id: str,
    db: AsyncSession = Depends(get_meeting_db),
):
    service = MeetingService(db)
    return await service.get_meeting(uuid.UUID(meeting_id))
