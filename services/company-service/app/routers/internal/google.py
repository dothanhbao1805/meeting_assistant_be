from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_company_db
from app.services import company_service
from app.services.google_calendar import get_valid_access_token

router = APIRouter(prefix="/internal/companies", tags=["internal"])


class GoogleCredentialsResponse(BaseModel):
    google_access_token: str
    google_calendar_id: str


@router.get("/{company_id}/google/credentials", response_model=GoogleCredentialsResponse)
async def get_google_credentials(
    company_id: str,
    db: AsyncSession = Depends(get_company_db),
):
    company = await company_service.get_company_by_id(db, company_id)

    if not company.google_calendar_id:
        raise HTTPException(status_code=400, detail="Google calendar not selected")

    access_token = await get_valid_access_token(company, db)
    return {
        "google_access_token": access_token,
        "google_calendar_id": company.google_calendar_id,
    }
