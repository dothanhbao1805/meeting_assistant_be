import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_auth_db 
from app.services import user_service

router = APIRouter(prefix="/internal/users", tags=["internal"])


@router.get("/{user_id}")
async def get_user_internal(
    user_id: str,
    db: AsyncSession = Depends(get_auth_db),
):
    return await user_service.get_user_by_id(db, user_id)

@router.get("/{user_id}")
async def get_user_internal(user_id: str, db: AsyncSession = Depends(get_auth_db)):
    return await user_service.get_user_by_id(db, user_id)