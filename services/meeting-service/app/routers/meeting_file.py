from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_meeting_db
from app.schemas.meeting_file import MeetingFileResponse
from app.services import meeting_file_service


router = APIRouter(prefix="/meeting-files", tags=["meeting-files"])

@router.get("/{meeting_file_id}", response_model=MeetingFileResponse)
async def get_meeting_file_by_id(meeting_file_id: str, db: AsyncSession = Depends(get_meeting_db)):
    return await meeting_file_service.get_meeting_file_by_id(db, meeting_file_id)