from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_superuser
from app.modules.users.model import User
from app.modules.users.schemas import (
    PasswordReset,
    SuccessResponse,
    UserCreate,
    UserListResponse,
    UserRead,
    UserUpdate,
)
from app.modules.users.service import UserService

router = APIRouter()


@router.get("", response_model=UserListResponse)
def list_users(
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> UserListResponse:
    return UserService(db).list_users(keyword, page, page_size)


@router.post("", response_model=UserRead)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    return UserService(db).create_user(payload)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    return UserService(db).get_user(user_id)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    return UserService(db).update_user(user_id, payload)


@router.delete("/{user_id}", response_model=SuccessResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> SuccessResponse:
    UserService(db).delete_user(user_id, current_user)
    return SuccessResponse()


@router.post("/{user_id}/reset-password", response_model=SuccessResponse)
def reset_password(
    user_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> SuccessResponse:
    UserService(db).reset_password(user_id, payload)
    return SuccessResponse()


@router.post("/{user_id}/toggle-active", response_model=UserRead)
def toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    return UserService(db).toggle_active(user_id, current_user)
