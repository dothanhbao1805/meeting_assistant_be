from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional
from uuid import UUID

from app.db.database import get_company_db
from app.schemas.member import MemberListResponse, MemberUpdate, MemberResponse
from app.services import member_service

router = APIRouter(prefix="/members", tags=["members"])

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
}

@router.post(
    "",
    response_model=MemberResponse,
    status_code=201,
    summary="Tạo member mới (kèm voice embedding tuỳ chọn)",
)
async def create_member(
    company_id: Annotated[UUID, Form()],
    account_id: Annotated[UUID, Form()],
    full_name: Annotated[str, Form()],
    role: Annotated[str, Form()],
    trello_user_id: Annotated[Optional[str], Form()] = None,
    trello_username: Annotated[Optional[str], Form()] = None,
    google_email: Annotated[Optional[str], Form()] = None,

    voice_file_1: Optional[UploadFile] = File(None),
    voice_file_2: Optional[UploadFile] = File(None),
    voice_file_3: Optional[UploadFile] = File(None),

    db: AsyncSession = Depends(get_company_db),
):
    try:
        raw_files = [f for f in [voice_file_1, voice_file_2, voice_file_3] if f is not None]

        audio_bytes_list = None

        if raw_files:
            audio_bytes_list = []
            for i, f in enumerate(raw_files):
                content = await f.read()
                if len(content) == 0:
                    raise HTTPException(status_code=400, detail=f"File {f.filename} is empty")

                audio_bytes_list.append(content)

        result = await member_service.create_member(
            db=db,
            company_id=company_id,
            account_id=account_id,
            full_name=full_name,
            role=role,
            trello_user_id=trello_user_id,
            trello_username=trello_username,
            google_email=google_email,
            audio_bytes_list=audio_bytes_list,
        )

        return result

    except HTTPException as e:
        print("❌ HTTP ERROR:", e.detail)
        raise e

    except Exception as e:
        import traceback

        print("🔥 UNEXPECTED ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.get("", response_model=MemberListResponse)
async def get_all_members(
    db: AsyncSession = Depends(get_company_db),
    company_id: UUID | None = None,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    role: str | None = None,
):
    return await member_service.get_all_members(
        db, company_id=company_id,
        page=page, page_size=page_size,
        search=search, role=role,
    )


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member_by_id(member_id: str, db: AsyncSession = Depends(get_company_db)):
    return await member_service.get_member_by_id(db, member_id)


@router.get("/account/{account_id}", response_model=MemberResponse)
async def get_member_by_account_id(account_id: UUID, db: AsyncSession = Depends(get_company_db)):
    member = await member_service.get_member_by_account_id(db, account_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found for this account")
    return member


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: str,

    full_name: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    google_email: Optional[str] = Form(None),
    trello_user_id: Optional[str] = Form(None),
    trello_username: Optional[str] = Form(None),

    voice_file_1: Optional[UploadFile] = File(None),
    voice_file_2: Optional[UploadFile] = File(None),
    voice_file_3: Optional[UploadFile] = File(None),

    db: AsyncSession = Depends(get_company_db),
):
    try:
        # Tạo object update data
        data = MemberUpdate(
            full_name=full_name,
            role=role,
            google_email=google_email,
            trello_user_id=trello_user_id,
            trello_username=trello_username,
        )

        # Lọc file không null
        raw_files = [
            f for f in [
                voice_file_1,
                voice_file_2,
                voice_file_3,
            ]
            if f is not None
        ]

        audio_bytes_list: list[bytes] | None = None

        if raw_files:
            ALLOWED_AUDIO_TYPES = {
                "audio/mpeg",
                "audio/wav",
                "audio/x-wav",
                "audio/mp4",
                "audio/webm",
            }

            audio_bytes_list = []

            for f in raw_files:

                # Validate mime type
                if f.content_type not in ALLOWED_AUDIO_TYPES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported audio type: {f.content_type}"
                    )

                content = await f.read()

                # Validate empty file
                if len(content) == 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {f.filename} is empty"
                    )

                audio_bytes_list.append(content)

        result = await member_service.update_member(
            db=db,
            member_id=member_id,
            data=data,
            audio_bytes_list=audio_bytes_list,
        )

        return result

    except HTTPException as e:
        print("❌ HTTP ERROR:", e.detail)
        raise e

    except Exception as e:
        import traceback

        print("🔥 UNEXPECTED ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@router.delete("/{member_id}", status_code=204)
async def delete_member(member_id: str, db: AsyncSession = Depends(get_company_db)):
    await member_service.delete_member(db, member_id)

