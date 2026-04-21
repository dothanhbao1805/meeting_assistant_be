from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transcript, TranscriptionJob, Utterance

async def get_latest_done_job_with_transcript(
    db: AsyncSession,
    meeting_id: UUID,
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


async def get_transcript_by_id(db: AsyncSession, transcript_id: UUID) -> Optional[Transcript]:
    stmt = (
        select(Transcript)
        .where(Transcript.id == transcript_id)
        .options(selectinload(Transcript.utterances))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_transcript_edited_text(
    db: AsyncSession,
    transcript_id: UUID,
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
    transcript_id: UUID,
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


async def get_utterance_by_id(db: AsyncSession, utterance_id: UUID) -> Optional[Utterance]:
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
    utterance_id: UUID,
    resolved_user_id: UUID,
    apply_to_all_same_label: bool,
    transcript_id: Optional[UUID],
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