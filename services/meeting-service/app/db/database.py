from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_async_engine(settings.MEETING_DATABASE_URL)
MeetingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

MeetingBase = declarative_base()


async def get_meeting_db():
    async with MeetingSessionLocal() as session:
        yield session
