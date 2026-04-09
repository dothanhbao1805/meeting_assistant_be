from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.services.WebServices import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, data)


# Chỉ admin xem được danh sách tất cả user
@router.get("/", response_model=list[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    return user_service.get_all_users(db)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.moderator)),
):
    user_service.delete_user(db, user_id)
