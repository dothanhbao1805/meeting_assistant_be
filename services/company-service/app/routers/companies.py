import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_company_db
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_company_db)):
    """Create a new company"""
    return await company_service.create_company(db, data)
