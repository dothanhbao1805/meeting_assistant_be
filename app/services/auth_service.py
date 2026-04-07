from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    refresh_token_expires_at,
    verify_password,
)
from app.repositories import token_repo, user_repo
from app.schemas.auth import LoginRequest, TokenResponse

token_blacklist: set[str] = set()


def _build_token_response(db: Session, user_id) -> TokenResponse:
    """Tạo cặp access + refresh token, lưu refresh vào DB"""
    access_token = create_access_token({"sub": str(user_id)})
    refresh_token = generate_refresh_token()
    expires_at = refresh_token_expires_at()
    token_repo.create_refresh_token(db, user_id, refresh_token, expires_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = user_repo.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa"
        )

    return _build_token_response(db, user.id)


def refresh(db: Session, refresh_token: str) -> TokenResponse:
    db_token = token_repo.get_by_token(db, refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn",
        )
    # Rotation: thu hồi token cũ, cấp cặp token mới
    token_repo.revoke_token(db, db_token)
    return _build_token_response(db, db_token.user_id)


def logout(db: Session, access_token: str, refresh_token: str | None = None) -> None:
    token_blacklist.add(access_token)
    if refresh_token:
        db_token = token_repo.get_by_token(db, refresh_token)
        if db_token:
            token_repo.revoke_token(db, db_token)


def logout_all(db: Session, access_token: str, user_id) -> None:
    """Đăng xuất tất cả thiết bị"""
    token_blacklist.add(access_token)
    token_repo.revoke_all_user_tokens(db, user_id)
