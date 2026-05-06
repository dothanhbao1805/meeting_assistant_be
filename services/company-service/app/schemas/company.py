from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    slug: str
    trello_token: Optional[str] = None
    trello_api_key: Optional[str] = None
    trello_workspace_id: Optional[str] = None
    owner_account_id: UUID


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    trello_token: Optional[str] = None
    trello_api_key: Optional[str] = None
    trello_workspace_id: Optional[str] = None
    status: Optional[str] = None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: Optional[str]
    trello_api_key: Optional[str]
    trello_token: Optional[str]
    trello_workspace_id: Optional[str]
    owner_account_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
