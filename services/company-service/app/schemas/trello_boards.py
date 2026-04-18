import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl


class TrelloBoardCreate(BaseModel):
    company_id: uuid.UUID
    trello_board_id: str
    name: str
    trello_url: str | None = None
    synced_at: datetime | None = None


class TrelloBoardUpdate(BaseModel):
    name: str | None = None
    trello_url: str | None = None
    synced_at: datetime | None = None


class TrelloBoardResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    trello_board_id: str
    name: str
    trello_url: str | None
    synced_at: datetime | None

    model_config = {"from_attributes": True}


class TrelloSyncRequest(BaseModel):
    company_id: uuid.UUID
    trello_api_key: str
    trello_token: str


class TrelloSyncResponse(BaseModel):
    synced_count: int
    created_boards: list[TrelloBoardResponse]
    skipped_boards: int