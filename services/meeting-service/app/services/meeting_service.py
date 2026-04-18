import hashlib
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from storage3 import create_client as create_storage_client

from app.core.config import settings
from app.models import Meeting, MeetingFile, MeetingParticipant
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.meeting import MeetingCreate


class MeetingService:
    def __init__(self, db: AsyncSession):
        self.repo = MeetingRepository(db)
        self.db = db
        self.storage = create_storage_client(
            f"{settings.SUPABASE_URL}/storage/v1/",
            {
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            },
            is_async=False,
        )

    async def create_meeting_with_file(
        self,
        data: MeetingCreate,
        file: UploadFile,
        current_user_id: uuid.UUID,
    ) -> Meeting:
        content = await file.read()
        checksum = hashlib.sha256(content).hexdigest()
        file_ext = file.filename.split(".")[-1].lower()
        storage_path = f"{current_user_id}/{uuid.uuid4()}.{file_ext}"

        try:
            self.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=storage_path,
                file=content,
                file_options={"content-type": file.content_type},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload that bai: {e}")

        public_url = self.storage.from_(settings.SUPABASE_BUCKET).get_public_url(
            storage_path
        )

        meeting = await self.repo.create(
            Meeting(
                company_id=data.company_id,
                created_by_user_id=current_user_id,
                title=data.title,
                status="uploaded",
                scheduled_at=data.scheduled_at,
                language_code=data.language_code or "vi",
            )
        )

        for user_id in set([*(data.participant_user_ids or []), current_user_id]):
            await self.repo.add_participant(
                MeetingParticipant(
                    meeting_id=meeting.id,
                    user_id=user_id,
                )
            )

        await self.repo.add_file(
            MeetingFile(
                meeting_id=meeting.id,
                storage_path=public_url,
                storage_bucket=settings.SUPABASE_BUCKET,
                file_type=file_ext,
                file_size_bytes=len(content),
                checksum_sha256=checksum,
            )
        )

        await self.db.commit()
        created_meeting = await self.repo.get_by_id(meeting.id)
        if not created_meeting:
            raise HTTPException(status_code=500, detail="Khong tai lai duoc meeting sau khi tao")
        return created_meeting

    async def get_meeting(self, meeting_id: uuid.UUID) -> Meeting:
        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting khong ton tai")
        return meeting

    async def get_meetings_by_company(self, company_id: uuid.UUID) -> list[Meeting]:
        return await self.repo.get_by_company(company_id)
