from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_company_db
from app.schemas.company import CompanyResponse
from app.schemas.google_calendar import (
    GoogleAuthorizeResponse,
    GoogleCalendarsResponse,
    GoogleCalendarSelection,
)
from app.services import company_service
from app.services import google_calendar as google_calendar_service

router = APIRouter(prefix="/companies", tags=["google-calendar"])


@router.get("/{company_id}/google/authorize", response_model=GoogleAuthorizeResponse)
async def google_authorize(
    company_id: str,
    db: AsyncSession = Depends(get_company_db),
):
    await company_service.get_company_by_id(db, company_id)
    return {"auth_url": google_calendar_service.build_google_auth_url(company_id)}


@router.post("/{company_id}/google/callback", response_model=CompanyResponse)
async def google_callback(
    company_id: str,
    code: str,
    db: AsyncSession = Depends(get_company_db),
):
    await company_service.get_company_by_id(db, company_id)
    return await google_calendar_service.exchange_code_for_tokens(db, company_id, code)


@router.get("/{company_id}/google/calendars", response_model=GoogleCalendarsResponse)
async def get_google_calendars(
    company_id: str,
    db: AsyncSession = Depends(get_company_db),
):
    company = await company_service.get_company_by_id(db, company_id)
    calendars = await google_calendar_service.fetch_google_calendars(company, db)
    return {"calendars": calendars}


@router.put("/{company_id}/google/calendar", response_model=CompanyResponse)
async def update_google_calendar(
    company_id: str,
    data: GoogleCalendarSelection,
    db: AsyncSession = Depends(get_company_db),
):
    await company_service.get_company_by_id(db, company_id)
    return await google_calendar_service.save_selected_calendar(
        db, company_id, data.calendar_id
    )
