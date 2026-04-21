from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import meeting_file_repository
from app.models.meeting_file import MeetingFile
from fastapi import HTTPException, status

async def get_meeting_file_by_id(db: AsyncSession, meeting_file_id: str) -> MeetingFile:
    result  = await meeting_file_repository.get_meeting_file_repository_by_id(db, meeting_file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting file not found",
        )
    return result
