from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_async_engine(os.getenv("AUTH_DATABASE_URL"))
AuthSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

AuthBase = declarative_base()


async def get_auth_db():
    async with AuthSessionLocal() as session:
        yield session
