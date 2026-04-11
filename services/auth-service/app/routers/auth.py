from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_auth_db
from app.db.database import get_auth_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_auth_db)):
    return await auth_service.login(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_auth_db)):
    return await auth_service.refresh(db, data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    data: RefreshRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_auth_db),
):
    await auth_service.logout(db, credentials.credentials, data.refresh_token)


@router.post("/logout-all", status_code=204)
async def logout_all(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_auth_db),
):
    await auth_service.logout_all(db, credentials.credentials, current_user.id)
