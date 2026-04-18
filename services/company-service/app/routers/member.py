from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_company_db
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse
from app.services import member_service

router = APIRouter(prefix="/members", tags=["members"])


@router.post("", response_model=MemberResponse, status_code=201)
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_company_db)):
    return await member_service.create_member(db, data)


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