import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.meeting_file import MeetingFile

class MeetingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, meeting: Meeting) -> Meeting:
        self.db.add(meeting)
        await self.db.flush()  # lấy id mà chưa commit
        return meeting

    async def add_participant(self, participant: MeetingParticipant):
        self.db.add(participant)

    async def add_file(self, meeting_file: MeetingFile):
        self.db.add(meeting_file)

    async def get_by_id(self, meeting_id: uuid.UUID) -> Meeting | None:
        result = await self.db.execute(
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.participants),
                selectinload(Meeting.files),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_company(self, company_id: uuid.UUID) -> list[Meeting]:
        result = await self.db.execute(
            select(Meeting)
            .where(Meeting.company_id == company_id)
            .options(
                selectinload(Meeting.participants),
                selectinload(Meeting.files),
            )
        )
        return result.scalars().all()