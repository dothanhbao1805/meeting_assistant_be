import uuid
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.utterance import UtteranceResponse, UtteranceUpdateResolved
from app.services.utterance_service import UtteranceService
from app.repositories.utterance_repo import UtteranceRepo

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
