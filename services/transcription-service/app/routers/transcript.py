from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
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
from app.schemas.auto_resolve import (
    AutoResolveRequest,
    AutoResolveResponse,
)

from app.services import transcript_service, auto_resolve_service

router = APIRouter(prefix="/api/v1", tags=["Transcripts"])


# ─── 1. GET meeting transcript ────────────────────────────────────────────────


@router.get(
    "/meetings/{meeting_id}/transcript",
    response_model=MeetingTranscriptResponse,
    summary="Lấy transcript theo meeting",
    responses={
        200: {"description": "Transcript đầy đủ kèm utterances"},
        404: {"description": "Không tìm thấy job hoặc transcript"},
        409: {"description": "Job chưa hoàn thành — kèm status hiện tại"},
    },
)
async def get_meeting_transcript(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> MeetingTranscriptResponse:
    return await transcript_service.get_meeting_transcript(db, meeting_id)


# ─── 2. GET utterances (paginated) ───────────────────────────────────────────


@router.get(
    "/transcripts/{transcript_id}/utterances",
    response_model=UtteranceListResponse,
    summary="Danh sách utterances có phân trang",
)
async def list_utterances(
    transcript_id: UUID,
    speaker_label: Optional[str] = Query(
        None, description="Lọc theo Speaker_0, Speaker_1..."
    ),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(50, ge=1, le=200, description="Số item mỗi trang"),
    db: AsyncSession = Depends(get_db),
) -> UtteranceListResponse:
    return await transcript_service.list_utterances(
        db, transcript_id, speaker_label, page, limit
    )


# ─── 3. PATCH transcript (edit full text) ────────────────────────────────────


@router.patch(
    "/transcripts/{transcript_id}",
    response_model=TranscriptResponse,
    summary="Chỉnh sửa edited_text của transcript",
    responses={
        200: {"description": "Transcript đã cập nhật với is_edited=true"},
        404: {"description": "Transcript không tồn tại"},
    },
)
async def update_transcript(
    transcript_id: UUID,
    payload: TranscriptUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TranscriptResponse:
    return await transcript_service.update_transcript(db, transcript_id, payload)


# ─── 5. PATCH resolve speaker ────────────────────────────────────────────────


@router.patch(
    "/utterances/{utterance_id}/resolve-speaker",
    response_model=UtteranceResolveSpeakerResponse,
    summary="Gán người nói (resolve speaker label → user)",
    responses={
        200: {"description": "updated_count — số utterances đã được gán"},
        404: {"description": "Utterance không tồn tại"},
    },
)
async def resolve_speaker(
    utterance_id: UUID,
    payload: UtteranceResolveSpeakerRequest,
    db: AsyncSession = Depends(get_db),
) -> UtteranceResolveSpeakerResponse:
    return await transcript_service.resolve_speaker(db, utterance_id, payload)


@router.post(
    "/transcripts/{transcript_id}/auto-resolve-speakers",
    response_model=AutoResolveResponse,
    summary="Tự động nhận diện và gán người nói từ voice embeddings",
)
async def auto_resolve_speakers(
    transcript_id: UUID,
    payload: AutoResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    token = request.headers.get("Authorization", "")
    return await auto_resolve_service.auto_resolve_speakers(
        db,
        transcript_id,
        str(payload.meeting_id),
        str(payload.company_id),
        str(payload.meeting_file_id),
        token=token,
    )
