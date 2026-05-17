from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.company import Company
from app.repositories import company_repo
from app.schemas.google_calendar import GoogleCalendarItem


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_LIST_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
]


def build_google_auth_url(company_id: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": company_id,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _token_expiry(expires_in: int | None) -> datetime:
    return datetime.utcnow() + timedelta(seconds=expires_in or 3600)


def _google_error(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text

    return data.get("error_description") or data.get("error") or response.text


async def exchange_code_for_tokens(
    db: AsyncSession, company_id: str, code: str
) -> Company:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_google_error(response),
        )

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token response missing access_token",
        )

    company = await company_repo.update_google_tokens(
        db=db,
        company_id=company_id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=_token_expiry(token_data.get("expires_in")),
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company


async def refresh_google_token(company: Company, db: AsyncSession) -> str:
    if not company.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account not connected",
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": company.google_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10.0,
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_google_error(response),
        )

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token response missing access_token",
        )

    await company_repo.update_google_tokens(
        db=db,
        company_id=str(company.id),
        access_token=access_token,
        refresh_token=None,
        token_expiry=_token_expiry(token_data.get("expires_in")),
    )
    return access_token


async def get_valid_access_token(company: Company, db: AsyncSession) -> str:
    if not company.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account not connected",
        )

    expires_at = company.google_token_expiry
    if expires_at and expires_at <= datetime.utcnow() + timedelta(minutes=1):
        return await refresh_google_token(company, db)

    return company.google_access_token


async def fetch_google_calendars(
    company: Company, db: AsyncSession
) -> list[GoogleCalendarItem]:
    access_token = await get_valid_access_token(company, db)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_CALENDAR_LIST_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch Google calendars: {_google_error(response)}",
        )

    data = response.json()
    calendars = []
    for item in data.get("items", []):
        calendars.append(
            GoogleCalendarItem(
                id=item["id"],
                name=item.get("summary") or item["id"],
                description=item.get("description"),
                is_primary=item.get("primary", False),
            )
        )

    return calendars


async def save_selected_calendar(
    db: AsyncSession, company_id: str, calendar_id: str
) -> Company:
    company = await company_repo.update_google_calendar_id(db, company_id, calendar_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
