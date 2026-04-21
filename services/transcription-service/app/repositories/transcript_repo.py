import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transcript import Transcript


class TranscriptRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Transcript:
        """Tạo transcript mới"""
        transcript = Transcript(
            job_id=uuid.UUID(data["job_id"]),
            meeting_id=uuid.UUID(data["meeting_id"]),
            full_text=data.get("full_text"),
            edited_text=data.get("edited_text"),
            is_edited=data.get("is_edited", False),
            speaker_count=data.get("speaker_count"),
            confidence_avg=data.get("confidence_avg"),
            language_detected=data.get("language_detected"),
            raw_deepgram_response=data.get("raw_deepgram_response"),
            created_at=datetime.utcnow(),
        )
        self.db.add(transcript)
        await self.db.flush()
        return transcript

    async def get_by_id(self, transcript_id: uuid.UUID) -> Transcript | None:
        """Lấy transcript theo ID"""
        result = await self.db.execute(
            select(Transcript).where(Transcript.id == transcript_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: uuid.UUID) -> Transcript | None:
        """Lấy transcript theo job_id (unique)"""
        result = await self.db.execute(
            select(Transcript).where(Transcript.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_meeting_id(self, meeting_id: uuid.UUID) -> list[Transcript]:
        """Lấy tất cả transcript của meeting"""
        result = await self.db.execute(
            select(Transcript).where(Transcript.meeting_id == meeting_id)
        )
        return list(result.scalars().all())

    async def update(
        self,
        transcript_id: uuid.UUID,
        data: dict,
    ) -> Transcript | None:
        """Cập nhật transcript"""
        transcript = await self.get_by_id(transcript_id)
        if not transcript:
            return None

        for key, value in data.items():
            if hasattr(transcript, key):
                setattr(transcript, key, value)

        await self.db.flush()
        return transcript
