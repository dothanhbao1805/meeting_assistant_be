import uuid
from datetime import datetime

from sqlalchemy import false
from sqlalchemy.orm import Session

from app.core.security import hash_refresh_token
from app.models.refresh_tokens import RefreshToken


def create_refresh_token(
    db: Session, user_id: uuid.UUID, token: str, expires_at: datetime
) -> RefreshToken:
    token_hash = hash_refresh_token(token)
    db_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_by_token(db: Session, token: str) -> RefreshToken | None:
    token_hash = hash_refresh_token(token)
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == false(),
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .first()
    )


def revoke_token(db: Session, db_token: RefreshToken) -> None:
    db_token.is_revoked = True
    db.commit()


def revoke_all_user_tokens(db: Session, user_id: uuid.UUID) -> None:
    """Dùng khi logout tất cả thiết bị"""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == false(),
    ).update({"is_revoked": True})
    db.commit()
