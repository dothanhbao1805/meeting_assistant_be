import uuid
import json
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.utterance import (
    UtteranceResponse,
    UtteranceUpdateRequest,
    UtteranceUpdateResolved,
    UtteranceUpdateByUser,
)
from app.services.utterance_service import UtteranceService
from app.repositories.utterance_repo import UtteranceRepo
from app.core.redis import redis_client


PENDING_REVIEW_KEY_PREFIX = "pending_review:meeting:"
CHANNEL_AUTO_RESOLVE_COMPLETED = "event:auto_resolve.completed"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utterances", tags=["Utterances"])


def get_utt_service(db: AsyncSession = Depends(get_db)) -> UtteranceService:
    return UtteranceService(UtteranceRepo(db))


@router.get("/transcript/{transcript_id}", response_model=List[UtteranceResponse])
async def get_utterances_by_transcript(
    transcript_id: uuid.UUID,
    service: UtteranceService = Depends(get_utt_service),
):
    """Lấy utterances theo transcript_id — dùng cho ai-analysis-service."""
    result = await service.get_utterances_by_transcript_id(transcript_id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy utterances")
    return result


@router.get(
    "/{meeting_id}/resolved-user-id-is-null", response_model=List[UtteranceResponse]
)
async def get_unresolved_utterances(
    meeting_id: uuid.UUID,
    service: UtteranceService = Depends(get_utt_service),
):
    """Lấy các utterances chưa được resolve speaker."""
    return await service.get_resolved_user_id_is_null(meeting_id)


@router.get("/{meeting_id}/all", response_model=List[UtteranceResponse])
async def get_all_utterances(
    meeting_id: uuid.UUID,
    service: UtteranceService = Depends(get_utt_service),
):
    """Lấy tất cả utterances của meeting."""
    return await service.get_all_utterances_by_meeting_id(meeting_id)


@router.patch("/{meeting_id}/resolve-speaker")
async def resolve_speaker(
    meeting_id: uuid.UUID,
    data: List[UtteranceUpdateResolved],
    service: UtteranceService = Depends(get_utt_service),
):
    """Map speaker_label → resolved_user_id cho toàn bộ meeting."""
    return await service.update_resolved_user_id_by_meeting_id_and_speaker_label(
        meeting_id, data
    )


@router.patch("/{meeting_id}/confirm-speakers")
async def confirm_speakers(
    meeting_id: uuid.UUID,
    data: List[UtteranceUpdateByUser],
    service: UtteranceService = Depends(get_utt_service),
):
    """User confirm/chỉnh sửa người nói từng câu → trigger ai-analyst pipeline."""
    result = await service.update_resolved_user_id_by_utterance_ids(meeting_id, data)

    redis_key = f"{PENDING_REVIEW_KEY_PREFIX}{meeting_id}"
    raw = await redis_client.get(redis_key)

    if raw is None:
        logger.warning(
            f"[confirm_speakers] No pending review state found for meeting={meeting_id}, "
            "skipping ai-analyst publish"
        )
        return result

    pending = json.loads(raw)
    await redis_client.publish(
        CHANNEL_AUTO_RESOLVE_COMPLETED,
        json.dumps(
            {
                "event": "auto_resolve.completed",
                "transcript_id": pending["transcript_id"],
                "meeting_id": pending["meeting_id"],
                "company_id": pending["company_id"],
                "meeting_file_id": pending["meeting_file_id"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    )
    logger.info(
        f"[confirm_speakers] Published auto_resolve.completed for meeting={meeting_id}"
    )
    await redis_client.delete(redis_key)

    return result


@router.patch(
    "/utterances/{utterance_id}",
    response_model=UtteranceResponse,
    summary="Sửa text của một utterance cụ thể",
)
async def update_utterance(
    utterance_id: uuid.UUID,
    payload: UtteranceUpdateRequest,
    service: UtteranceService = Depends(get_utt_service),
) -> UtteranceResponse:
    return await service.update_utterance(utterance_id, payload)
