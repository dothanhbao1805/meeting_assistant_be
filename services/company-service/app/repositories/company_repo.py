from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import  select
from app.models.company import Company


async def get_company_by_id(db: AsyncSession, company_id: str) -> Company | None:
    result = await db.execute(select(Company).where(Company.id == UUID(company_id)))
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
        company.trello_api_key = data.get("trello_api_key", company.trello_api_key)
        company.trello_workspace_id = data.get("trello_workspace_id", company.trello_workspace_id)
        company.google_calendar_id = data.get("google_calendar_id", company.google_calendar_id)
        company.owner_account_id = data.get("owner_account_id", company.owner_account_id)
        company.logo_url = data.get("logo_url", company.logo_url)
        company.status = data.get("status", company.status)

        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company
    
async def update_trello_key(db: AsyncSession, company_id: str, trello_api_key: str, trello_workspace_id: str) -> Company:
    company = await get_company_by_id(db, company_id)
    if company:
        company.trello_api_key = trello_api_key
        company.trello_workspace_id = trello_workspace_id

        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company    

async def update_google_tokens(
    db: AsyncSession,
    company_id: str,
    access_token: str,
    refresh_token: str | None,
    token_expiry: datetime,
) -> Company | None:
    company = await get_company_by_id(db, company_id)
    if company:
        company.google_access_token = access_token
        if refresh_token:
            company.google_refresh_token = refresh_token
        company.google_token_expiry = token_expiry

        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company


async def update_google_calendar_id(
    db: AsyncSession, company_id: str, calendar_id: str
) -> Company | None:
    company = await get_company_by_id(db, company_id)
    if company:
        company.google_calendar_id = calendar_id

        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company    

async def delete_company(db: AsyncSession, company_id: str) -> None:
    company = await get_company_by_id(db, company_id)
    if company:
        await db.delete(company)
        await db.commit()           


async def get_company_by_owner(db: AsyncSession, account_id: UUID):
    result = await db.execute(
        select(Company).where(Company.owner_account_id == account_id)
    )
    return result.scalar_one_or_none()
