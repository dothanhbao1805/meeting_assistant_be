from datetime import date, timedelta
from urllib.parse import quote

import httpx


GOOGLE_CALENDAR_BASE_URL = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarClient:
    def __init__(self, access_token: str):
        self.access_token = access_token

    async def create_all_day_event(
        self,
        calendar_id: str,
        title: str,
        description: str | None,
        due_date: date,
        attendee_email: str | None = None,
    ) -> dict:
        event = {
            "summary": title,
            "description": description or "",
            "start": {"date": due_date.isoformat()},
            "end": {"date": (due_date + timedelta(days=1)).isoformat()},
        }

        if attendee_email:
            event["attendees"] = [{"email": attendee_email}]

        encoded_calendar_id = quote(calendar_id, safe="")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GOOGLE_CALENDAR_BASE_URL}/calendars/{encoded_calendar_id}/events",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=event,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
