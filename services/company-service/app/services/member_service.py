from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.models.member import Member
from app.repositories import member_repo
from app.schemas.member import MemberUpdate
from app.utils.voice_embedding import compute_embedding_from_bytes, average_embeddings


async def create_member(
    db: AsyncSession,
    company_id: UUID,
    account_id: UUID,
    full_name: str,
    role: str,
    trello_user_id: Optional[str] = None,
    trello_username: Optional[str] = None,
    google_email: Optional[str] = None,
    audio_bytes_list: Optional[List[bytes]] = None,
) -> Member:
    # Tính voice embedding nếu có file audio
    voice_embedding = None
    if audio_bytes_list:
        embeddings = [compute_embedding_from_bytes(b) for b in audio_bytes_list]
        voice_embedding = average_embeddings(embeddings)

    data = {
        "company_id": company_id,
        "account_id": account_id,
        "full_name": full_name,
        "role": role,
        "trello_user_id": trello_user_id,
        "trello_username": trello_username,
        "google_email": google_email,
        "voice_embedding": voice_embedding,
    }
    return await member_repo.create_member(db, data)


async def get_member_by_id(db: AsyncSession, member_id: str) -> Member:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member


async def get_all_members(
    db: AsyncSession,
    company_id: UUID | None = None,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    role: str | None = None,
) -> dict:
    return await member_repo.get_all_members(
        db, company_id=company_id,
        page=page, page_size=page_size,
        search=search, role=role,
    )


async def get_member_by_account_id(db: AsyncSession, account_id: UUID) -> Optional[Member]:
    return await member_repo.get_member_by_account_id(db, account_id)


async def update_member(
    db: AsyncSession,
    member_id: str,
    data: MemberUpdate,
    audio_bytes_list: list | None = None,
) -> Member:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cập nhật các field có giá trị
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(member, field, value)

    # Cập nhật voice embedding nếu có file mới
    if audio_bytes_list:
        embeddings = [
            compute_embedding_from_bytes(b)
            for b in audio_bytes_list
        ]

        member.voice_embedding = average_embeddings(embeddings)

    try:
        await db.commit()
        await db.refresh(member)

    except Exception:
        await db.rollback()
        raise
    
    return member


async def delete_member(db: AsyncSession, member_id: str) -> None:
    member = await member_repo.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    await member_repo.delete_member(db, member_id)