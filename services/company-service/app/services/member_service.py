from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.repositories import member_repo
from app.schemas.member import MemberCreate, MemberUpdate


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    return await member_repo.create_member(db, data.model_dump())   


async def get_member_by_id(db: AsyncSession, member_id: str) -> Member:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member


async def get_all_members(db: AsyncSession) -> list[Member]:
    return await member_repo.get_all_members(db)


async def update_member(db: AsyncSession, member_id: str, data: MemberUpdate) -> Member:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    updated_member = await member_repo.update_member(db, member_id, data)
    return updated_member


async def delete_member(db: AsyncSession, member_id: str) -> None:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    await member_repo.delete_member(db, member_id)