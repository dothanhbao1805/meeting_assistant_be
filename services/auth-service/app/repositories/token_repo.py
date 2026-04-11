import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql.expression import false

from app.core.security import hash_refresh_token
from app.models.refresh_tokens import RefreshToken


async def create_refresh_token(
    db: AsyncSession, user_id: uuid.UUID, token: str, expires_at: datetime
) -> RefreshToken:
    token_hash = hash_refresh_token(token)
    db_token = RefreshToken(
        user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def get_by_token(db: AsyncSession, token: str) -> RefreshToken | None:
    token_hash = hash_refresh_token(token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == false(),
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    return result.scalar_one_or_none()


async def revoke_token(db: AsyncSession, db_token: RefreshToken) -> None:
    db_token.is_revoked = True
    await db.commit()


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    from sqlalchemy import update

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == false())
        .values(is_revoked=True)
    )
    await db.commit()
