from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting_file import MeetingFile
from sqlalchemy import select

async def get_meeting_file_repository_by_id(db: AsyncSession, meeting_file_id: str) -> MeetingFile|None:
    result = await db.execute(select(MeetingFile).where(MeetingFile.id == meeting_file_id))
    return result.scalar_one_or_none()
