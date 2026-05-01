from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.deps import (
    CurrentUser,
    get_current_active_user,
    get_raw_token,
)
from app.services.speaker_service import SpeakerService
from app.schemas.speaker import SpeakerResolveRequest
from typing import List

router = APIRouter(prefix="/speakers", tags=["speakers"])


def get_speaker_service() -> SpeakerService:
    return SpeakerService()


@router.get("/{meeting_id}/unresolved-speakers")
async def get_unresolved_speakers(
    meeting_id: UUID,
    user: CurrentUser = Depends(get_current_active_user),
    token: str = Depends(get_raw_token),
    service: SpeakerService = Depends(get_speaker_service),
):
    return await service.get_unresolved_logic(meeting_id, token)


@router.patch("/{meeting_id}/unresolved-speakers")
async def resolve_unresolved_speakers(
    meeting_id: UUID,
    payload: List[SpeakerResolveRequest],
    user = Depends(get_current_active_user),
    token: str = Depends(get_raw_token),
    service: SpeakerService = Depends()
):
    return await service.patch_resolve_logic(
        meeting_id=meeting_id,
        payload=payload,
        token=token
    )