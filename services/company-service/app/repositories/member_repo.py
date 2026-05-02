import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import Member


async def get_member_by_id(db: AsyncSession, member_id: str) -> Member | None:
    result = await db.execute(select(Member).where(Member.id == uuid.UUID(member_id)))
    return result.scalar_one_or_none()


async def get_all_members(db: AsyncSession) -> list[Member]:
    result = await db.execute(select(Member))
    return result.scalars().all()


async def create_member(db: AsyncSession, data: dict) -> Member:
    member = Member(**data)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

async def update_member(db: AsyncSession, member_id: str, data: dict) -> Member:
    member = await get_member_by_id(db, member_id)
    if member:
        member.name = data.get("name", member.name)
        member.email = data.get("email", member.email)
        member.company_id = data.get("company_id", member.company_id)

        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

async def delete_member(db: AsyncSession, member_id: str) -> None:
    member = await get_member_by_id(db, member_id)
    if member:
        await db.delete(member)
        await db.commit()

async def get_by_account_id(db: AsyncSession, account_id: str):
    result = await db.execute(
        select(Member).where(Member.id == account_id)  # đổi account_id → id
    )
    return result.scalar_one_or_none()