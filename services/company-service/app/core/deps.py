from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_company_db


async def get_db() -> AsyncSession:
    async with __import__("app.db.database", fromlist=["CompanySessionLocal"]).CompanySessionLocal() as session:
        yield session
