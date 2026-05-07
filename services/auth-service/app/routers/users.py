from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import httpx
from app.core.config import settings
from app.core.deps import get_current_user, get_auth_db, require_role
from app.db.database import get_auth_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserMeResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    # Create base response from current user
    me_data = UserMeResponse.model_validate(current_user)

    # Call Company Service to get member info
    try:
        async with httpx.AsyncClient() as client:
            url = f"{settings.COMPANY_SERVICE_URL}/api/v1/members/account/{current_user.id}"
            response = await client.get(url, timeout=5.0)
            
            if response.status_code == 200:
                member_info = response.json()
                me_data.company_id = member_info.get("company_id")
                me_data.member_role = member_info.get("role")
                me_data.is_trello_linked = bool(member_info.get("trello_user_id"))
                me_data.is_google_linked = bool(member_info.get("google_email"))
    except Exception as e:
        print(f"Error fetching company info for user {current_user.id}: {str(e)}")

    return me_data


@router.post("/register", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_auth_db)):
    return await user_service.create_user(db, data)


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_auth_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return await user_service.get_all_users(db)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_auth_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.moderator)),
):
    await user_service.delete_user(db, user_id)
