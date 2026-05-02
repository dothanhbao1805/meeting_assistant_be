from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await user_repo.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng",
        )
    hashed = hash_password(data.password)
    return await user_repo.create_user(db, data.email, hashed, data.full_name)


async def get_all_users(db: AsyncSession) -> list[User]:
    return await user_repo.get_all_users(db)


async def delete_user(db: AsyncSession, user_id: str) -> None:
    await user_repo.delete_user(db, user_id)

async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User không tồn tại",
        )
    return user