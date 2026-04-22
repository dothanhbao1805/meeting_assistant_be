from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


bearer_scheme = HTTPBearer()


@dataclass
class CurrentUser:
    id: UUID
    email: str | None = None
    role: str = "user"
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token da het han",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token khong hop le",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return CurrentUser(
            id=UUID(payload["sub"]),
            email=payload.get("email"),
            role=payload.get("role", "user"),
            full_name=payload.get("full_name"),
            is_active=payload.get("is_active", True),
            is_superuser=payload.get("is_superuser", False),
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token thieu thong tin bat buoc: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tai khoan da bi vo hieu hoa",
        )
    return current_user


def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Khong co quyen thuc hien thao tac nay",
        )
    return current_user
