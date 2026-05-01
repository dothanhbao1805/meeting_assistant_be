from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional
from uuid import UUID

from app.db.database import get_company_db
from app.schemas.member import MemberUpdate, MemberResponse
from app.services import member_service

router = APIRouter(prefix="/members", tags=["members"])


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
        print("🚀 START create_member")

        # ===== DEBUG INPUT =====
        print("👉 company_id:", company_id)
        print("👉 account_id:", account_id)
        print("👉 full_name:", full_name)
        print("👉 role:", role)

        # ===== HANDLE FILE =====
        raw_files = [f for f in [voice_file_1, voice_file_2, voice_file_3] if f is not None]

        print(f"👉 Number of files received: {len(raw_files)}")

        audio_bytes_list = None

        if raw_files:
            audio_bytes_list = []
            for i, f in enumerate(raw_files):
                content = await f.read()
                print(f"👉 File {i+1}: name={f.filename}, size={len(content)} bytes")

                if len(content) == 0:
                    raise HTTPException(status_code=400, detail=f"File {f.filename} is empty")

                audio_bytes_list.append(content)

        print("👉 Calling member_service.create_member...")

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

        print("✅ SUCCESS create_member")

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


@router.get("", response_model=list[MemberResponse])
async def get_all_members(db: AsyncSession = Depends(get_company_db)):
    return await member_service.get_all_members(db)


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member_by_id(member_id: str, db: AsyncSession = Depends(get_company_db)):
    return await member_service.get_member_by_id(db, member_id)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: str,
    data: MemberUpdate,
    db: AsyncSession = Depends(get_company_db),
):
    return await member_service.update_member(db, member_id, data)

@router.delete("/{member_id}", status_code=204)
async def delete_member(member_id: str, db: AsyncSession = Depends(get_company_db)):
    await member_service.delete_member(db, member_id)

