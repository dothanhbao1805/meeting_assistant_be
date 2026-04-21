import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.models.transcript import Transcript
from app.models.transcription_job import TranscriptionJob
from app.models.utterance import Utterance


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

async def get_latest_done_job_with_transcript(
    db: AsyncSession,
    meeting_id: uuid.UUID,
) -> Optional[Tuple[TranscriptionJob, Optional[Transcript]]]:
    stmt = (
        select(TranscriptionJob)
        .where(TranscriptionJob.meeting_id == meeting_id)
        .order_by(TranscriptionJob.started_at.desc().nullslast())
        .limit(1)
    )
    result = await db.execute(stmt)
    job: Optional[TranscriptionJob] = result.scalar_one_or_none()
    if job is None:
        return None

    if job.status != "done":
        return (job, None)

    # Lấy transcript mới nhất kèm utterances (eager load để tránh N+1)
    stmt2 = (
        select(Transcript)
        .where(Transcript.job_id == job.id)
        .options(selectinload(Transcript.utterances))
        .limit(1)
    )
    result2 = await db.execute(stmt2)
    transcript: Optional[Transcript] = result2.scalar_one_or_none()
    return (job, transcript)


async def get_transcript_by_id(db: AsyncSession, transcript_id: uuid.UUID) -> Optional[Transcript]:
    stmt = (
        select(Transcript)
        .where(Transcript.id == transcript_id)
        .options(selectinload(Transcript.utterances))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_transcript_edited_text(
    db: AsyncSession,
    transcript_id: uuid.UUID,
    edited_text: str,
) -> Optional[Transcript]:
    stmt = (
        update(Transcript)
        .where(Transcript.id == transcript_id)
        .values(edited_text=edited_text, is_edited=True)
        .returning(Transcript)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


# ─── Utterance queries ────────────────────────────────────────────────────────

async def get_utterances_paginated(
    db: AsyncSession,
    transcript_id: uuid.UUID,
    speaker_label: Optional[str],
    page: int,
    limit: int,
) -> Tuple[List[Utterance], int]:
    base_filter = [Utterance.transcript_id == transcript_id]
    if speaker_label:
        base_filter.append(Utterance.speaker_label == speaker_label)

    # Đếm total (tránh load toàn bộ dữ liệu)
    count_stmt = select(func.count()).select_from(Utterance).where(*base_filter)
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Lấy trang
    offset = (page - 1) * limit
    stmt = (
        select(Utterance)
        .where(*base_filter)
        .order_by(Utterance.sequence_order.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return list(items), total


async def get_utterance_by_id(db: AsyncSession, utterance_id: uuid.UUID) -> Optional[Utterance]:
    stmt = select(Utterance).where(Utterance.id == utterance_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_utterance_text(
    db: AsyncSession,
    utterance: Utterance,
    new_text: str,
) -> Utterance:
    if not utterance.is_edited:
        utterance.original_text = utterance.text  # snapshot bản gốc
    utterance.text = new_text
    utterance.is_edited = True
    await db.commit()
    await db.refresh(utterance)
    return utterance


async def resolve_speaker(
    db: AsyncSession,
    utterance_id: uuid.UUID,
    resolved_user_id: uuid.UUID,
    apply_to_all_same_label: bool,
    transcript_id: Optional[uuid.UUID],
    speaker_label: Optional[str],
) -> int:
    if apply_to_all_same_label and transcript_id and speaker_label:
        stmt = (
            update(Utterance)
            .where(
                Utterance.transcript_id == transcript_id,
                Utterance.speaker_label == speaker_label,
            )
            .values(resolved_user_id=resolved_user_id)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount  # type: ignore[return-value]
    else:
        stmt = (
            update(Utterance)
            .where(Utterance.id == utterance_id)
            .values(resolved_user_id=resolved_user_id)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount  # type: ignore[return-value]
