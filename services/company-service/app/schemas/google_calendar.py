from pydantic import BaseModel


class GoogleAuthorizeResponse(BaseModel):
    auth_url: str


class GoogleCalendarItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_primary: bool = False


class GoogleCalendarsResponse(BaseModel):
    calendars: list[GoogleCalendarItem]


class GoogleCalendarSelection(BaseModel):
    calendar_id: str
