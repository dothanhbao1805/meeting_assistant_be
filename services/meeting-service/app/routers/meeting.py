import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_meeting_db
from app.schemas.meeting import MeetingCreate, MeetingOut
from app.services.meeting_service import MeetingService


router = APIRouter(prefix="/meetings", tags=["meetings"])


def get_meeting_service(db: AsyncSession = Depends(get_meeting_db)) -> MeetingService:
    return MeetingService(db)


def parse_participant_user_ids(raw_value: Optional[str]) -> list[str]:
    if raw_value is None:
        return []

    value = raw_value.strip()
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = [item.strip() for item in value.split(",") if item.strip()]

    if not isinstance(parsed, list):
        raise HTTPException(status_code=422, detail="participant_user_ids phai la danh sach")

    return parsed


@router.post("/", response_model=MeetingOut, status_code=201)
async def create_meeting(
    title: str = Form(...),
    company_id: UUID = Form(...),
    scheduled_at: Optional[str] = Form(None),
    language_code: Optional[str] = Form("vi"),
    trello_board_id: Optional[str] = Form(None),
    trello_board_name: Optional[str] = Form(None),
    trello_list_id: Optional[str] = Form(None),
    participant_user_ids: Optional[str] = Form("[]"),
    file: UploadFile = File(...),
    service: MeetingService = Depends(get_meeting_service),
    current_user=Depends(get_current_user),
):
    participants = parse_participant_user_ids(participant_user_ids)

    data = MeetingCreate(
        title=title,
        company_id=company_id,
        scheduled_at=datetime.fromisoformat(scheduled_at) if scheduled_at else None,
        language_code=language_code,
        trello_board_id=trello_board_id,
        trello_board_name=trello_board_name,
        trello_list_id=trello_list_id,
        participant_user_ids=participants,
    )

    return await service.create_meeting_with_file(
        data=data,
        file=file,
        current_user_id=current_user.id,
    )


@router.get("/", response_model=List[MeetingOut])
async def list_meetings(
    company_id: UUID,
    service: MeetingService = Depends(get_meeting_service),
    current_user=Depends(get_current_user),
):
    return await service.get_meetings_by_company(company_id)


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: UUID,
    service: MeetingService = Depends(get_meeting_service),
    current_user=Depends(get_current_user),
):
    return await service.get_meeting(meeting_id)
