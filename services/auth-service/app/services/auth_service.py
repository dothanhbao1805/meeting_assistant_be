from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    refresh_token_expires_at,
    verify_password,
)
from app.core.deps import token_blacklist
from app.repositories import token_repo, user_repo
from app.schemas.auth import LoginRequest, TokenResponse


async def _build_token_response(db: AsyncSession, user_id) -> TokenResponse:
    access_token = create_access_token({"sub": str(user_id)})
    refresh_token = generate_refresh_token()
    expires_at = refresh_token_expires_at()
    await token_repo.create_refresh_token(db, user_id, refresh_token, expires_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await user_repo.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )
    return await _build_token_response(db, user.id)


async def refresh(db: AsyncSession, refresh_token: str) -> TokenResponse:
    db_token = await token_repo.get_by_token(db, refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn",
        )
    await token_repo.revoke_token(db, db_token)
    return await _build_token_response(db, db_token.user_id)


async def logout(
    db: AsyncSession, access_token: str, refresh_token: str | None = None
) -> None:
    token_blacklist.add(access_token)
    if refresh_token:
        db_token = await token_repo.get_by_token(db, refresh_token)
        if db_token:
            await token_repo.revoke_token(db, db_token)


async def logout_all(db: AsyncSession, access_token: str, user_id) -> None:
    token_blacklist.add(access_token)
    await token_repo.revoke_all_user_tokens(db, user_id)
