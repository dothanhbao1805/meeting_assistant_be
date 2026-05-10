from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_company_db
from app.repositories import member_repo

router = APIRouter(prefix="/internal/members", tags=["internal"])


class MemberInternal(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str] = None
    account_id: Optional[UUID] = None

    class Config:
        from_attributes = True


@router.get("/by-account/{account_id}", response_model=MemberInternal)
async def get_member_by_account(
    account_id: str,
    db: AsyncSession = Depends(get_company_db),
):
    member = await member_repo.get_by_account_id(db, account_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.get("/{member_id}", response_model=MemberInternal)
async def get_member_by_id(
    member_id: str,
    db: AsyncSession = Depends(get_company_db),
):
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member
