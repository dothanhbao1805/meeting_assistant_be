import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.company import Company


async def get_company_by_id(db: AsyncSession, company_id: str) -> Company | None:
    result = await db.execute(select(Company).where(Company.id == uuid.UUID(company_id)))
    return result.scalar_one_or_none()

async def get_company_by_slug(db: AsyncSession, slug: str) -> Company | None:
    result = await db.execute(select(Company).where(Company.slug == slug))
    return result.scalar_one_or_none()

async def get_all_companies(db: AsyncSession) -> list[Company]:             
    result = await db.execute(select(Company))
    return result.scalars().all()


async def create_company(db: AsyncSession, data: dict) -> Company:
    company = Company(**data)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def update_company(db: AsyncSession, company_id: str, data: dict) -> Company:
    company = await get_company_by_id(db, company_id)
    if company:
        company.name = data.get("name", company.name)
        company.slug = data.get("slug", company.slug)
        company.trello_token = data.get("trello_token", company.trello_token)
        company.trello_workspace_id = data.get("trello_workspace_id", company.trello_workspace_id)
        company.owner_account_id = data.get("owner_account_id", company.owner_account_id)
        company.logo_url = data.get("logo_url", company.logo_url)
        company.status = data.get("status", company.status)

        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company

async def delete_company(db: AsyncSession, company_id: str) -> None:
    company = await get_company_by_id(db, company_id)
    if company:
        await db.delete(company)
        await db.commit()           