from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_auth_db, require_role
from app.db.database import get_auth_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_auth_db)):
    return await user_service.create_user(db, data)


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_auth_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return await user_service.get_all_users(db)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_auth_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.moderator)),
):
    await user_service.delete_user(db, user_id)
