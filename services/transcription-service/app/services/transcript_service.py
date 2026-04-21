"""
transcript_service.py  — Business logic cho Read API & Editing Layer (Người 4)

Service layer chịu trách nhiệm:
- Xử lý rule nghiệp vụ (không overwrite full_text, kiểm tra quyền, v.v.)
- Gọi repository, không gọi DB trực tiếp
- Publish event sau khi resolve speaker (giao tiếp với Meeting Service)
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import transcript_repo
from app.schemas.transcript import (
    MeetingTranscriptResponse,
    TranscriptResponse,
    TranscriptUpdateRequest,
    UtteranceResponse,

)
from app.schemas.utterance import (
    UtteranceListResponse,
    UtteranceUpdateRequest,
    UtteranceResolveSpeakerRequest,
    UtteranceResolveSpeakerResponse,
)

logger = logging.getLogger(__name__)


async def get_meeting_transcript(
    db: AsyncSession,
    meeting_id: UUID,
) -> MeetingTranscriptResponse:
    row = await transcript_repo.get_latest_done_job_with_transcript(db, meeting_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transcription job found for meeting {meeting_id}",
        )

    job, transcript = row

    if job.status != "done":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Transcription is not yet complete",
                "job_id": str(job.id),
                "status": job.status,
            },
        )

    if transcript is None:
        # job done nhưng chưa có transcript — edge case, log để debug
        logger.warning("Job %s is done but transcript is missing", job.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found for completed job",
        )

    return MeetingTranscriptResponse(
        job_id=job.id,
        job_status=job.status,
        transcript=TranscriptResponse.model_validate(transcript),
    )


# ─── Utterances ───────────────────────────────────────────────────────────────

async def list_utterances(
    db: AsyncSession,
    transcript_id: UUID,
    speaker_label: Optional[str],
    page: int,
    limit: int,
) -> UtteranceListResponse:
    transcript = await transcript_repo.get_transcript_by_id(db, transcript_id)
    if transcript is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

    items, total = await transcript_repo.get_utterances_paginated(
        db, transcript_id, speaker_label, page, limit
    )
    return UtteranceListResponse(
        items=[UtteranceResponse.model_validate(u) for u in items],
        total=total,
        page=page,
        limit=limit,
        has_next=(page * limit) < total,
    )


async def update_utterance(
    db: AsyncSession,
    utterance_id: UUID,
    payload: UtteranceUpdateRequest,
) -> UtteranceResponse:
    utterance = await transcript_repo.get_utterance_by_id(db, utterance_id)
    if utterance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utterance not found")

    updated = await transcript_repo.update_utterance_text(db, utterance, payload.text)
    return UtteranceResponse.model_validate(updated)


async def resolve_speaker(
    db: AsyncSession,
    utterance_id: UUID,
    payload: UtteranceResolveSpeakerRequest,
) -> UtteranceResolveSpeakerResponse:
    utterance = await transcript_repo.get_utterance_by_id(db, utterance_id)
    if utterance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utterance not found")

    updated_count = await transcript_repo.resolve_speaker(
        db=db,
        utterance_id=utterance_id,
        resolved_user_id=payload.resolved_user_id,
        apply_to_all_same_label=payload.apply_to_all_same_label,
        transcript_id=utterance.transcript_id,
        speaker_label=utterance.speaker_label,
    )

    # Publish event cho Meeting Service (fire-and-forget, không block response)
    await _publish_speaker_resolved_event(
        transcript_id=utterance.transcript_id,
        speaker_label=utterance.speaker_label,
        resolved_user_id=payload.resolved_user_id,
    )

    label_info = f"speaker '{utterance.speaker_label}'" if payload.apply_to_all_same_label else "utterance"
    return UtteranceResolveSpeakerResponse(
        updated_count=updated_count,
        message=f"Resolved {updated_count} utterances for {label_info}",
    )


# ─── Transcript edit ──────────────────────────────────────────────────────────

async def update_transcript(
    db: AsyncSession,
    transcript_id: UUID,
    payload: TranscriptUpdateRequest,
) -> TranscriptResponse:
    """
    PATCH /api/v1/transcripts/{transcript_id}
    Chỉ cập nhật edited_text. full_text KHÔNG BAO GIỜ bị overwrite.
    """
    result = await transcript_repo.update_transcript_edited_text(
        db, transcript_id, payload.edited_text
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

    # Reload với utterances để trả về đầy đủ
    transcript = await transcript_repo.get_transcript_by_id(db, transcript_id)
    return TranscriptResponse.model_validate(transcript)


# ─── Internal helpers ─────────────────────────────────────────────────────────

async def _publish_speaker_resolved_event(
    transcript_id: UUID,
    speaker_label: Optional[str],
    resolved_user_id: UUID,
) -> None:
    """
    Publish event `speaker.resolved` để Meeting Service cập nhật meeting_participants.
    Implement bằng Redis Pub/Sub hoặc message broker tuỳ team quyết định.
    Đây là stub — thay bằng implementation thực tế của team.
    """
    try:
        event_payload = {
            "event": "speaker.resolved",
            "transcript_id": str(transcript_id),
            "speaker_label": speaker_label,
            "resolved_user_id": str(resolved_user_id),
        }
        logger.info("Publishing event: %s", event_payload)
        # TODO: await redis.publish("meeting_events", json.dumps(event_payload))
    except Exception as exc:
        # Không để lỗi publish event làm fail response chính
        logger.error("Failed to publish speaker resolved event: %s", exc)