import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UpdateUser(BaseModel):
    is_onboarded: bool 

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    role: UserRole
    is_onboarded: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    role: UserRole
    # Extra info from Company Service
    company_id: uuid.UUID | None = None
    member_role: str | None = None
    is_trello_linked: bool = False
    is_google_linked: bool = False

    model_config = {"from_attributes": True}
