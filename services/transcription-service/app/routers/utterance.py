from fastapi import APIRouter,Depends
from typing import List
from app.schemas.utterance import UtteranceResponse, UtteranceUpdateResolved
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
import uuid
from app.services.utterance_service import UtteranceService
from app.repositories.utterance_repo import UtteranceRepo


router = APIRouter(prefix="/utterances", tags=["Utterances"])

def get_utt_service(db: AsyncSession = Depends(get_db)) -> UtteranceService:
    repo = UtteranceRepo(db)
    return UtteranceService(repo)

@router.get("/{meeting_id}/resolved-user-id-is-null", response_model=List[UtteranceResponse])
async def get_resolved_user_id_is_null(meeting_id: uuid.UUID, service: UtteranceService = Depends(get_utt_service)):
    result = await service.get_resolved_user_id_is_null(meeting_id)
    return result

@router.get("/{meeting_id}/all", response_model=List[UtteranceResponse])
async def get_all_utterances_by_meeting_id(meeting_id: uuid.UUID, service: UtteranceService = Depends(get_utt_service)):
    result = await service.get_all_utterances_by_meeting_id(meeting_id)
    return result

@router.patch("/{meeting_id}/resolve-speaker")
async def update_resolved_user_id_by_meeting_id_and_speaker_label(
    meeting_id: uuid.UUID,
    data: List[UtteranceUpdateResolved],
    service: UtteranceService = Depends(get_utt_service)
):
    result = await service.update_resolved_user_id_by_meeting_id_and_speaker_label(meeting_id, data)
    return result