from fastapi import APIRouter, Depends, Query, Request
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
from app.modules.audit_logs.service import record_audit_log

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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    user = UserService(db).create_user(payload)
    record_audit_log(db, current_user, "users", "create", f"创建用户：{user.username}", "user", user.id, user.username, request)
    return user


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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    user = UserService(db).update_user(user_id, payload)
    record_audit_log(db, current_user, "users", "update", f"编辑用户：{user.username}", "user", user.id, user.username, request)
    return user


@router.delete("/{user_id}", response_model=SuccessResponse)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> SuccessResponse:
    user = UserService(db).get_user(user_id)
    UserService(db).delete_user(user_id, current_user)
    record_audit_log(db, current_user, "users", "delete", f"删除用户：{user.username}", "user", user.id, user.username, request)
    return SuccessResponse()


@router.post("/{user_id}/reset-password", response_model=SuccessResponse)
def reset_password(
    user_id: int,
    payload: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> SuccessResponse:
    UserService(db).reset_password(user_id, payload)
    record_audit_log(db, current_user, "users", "reset_password", f"重置用户密码：{user_id}", "user", user_id, str(user_id), request)
    return SuccessResponse()


@router.post("/{user_id}/toggle-active", response_model=UserRead)
def toggle_active(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> User:
    user = UserService(db).toggle_active(user_id, current_user)
    record_audit_log(db, current_user, "users", "toggle_active", f"启用禁用用户：{user.username}", "user", user.id, user.username, request)
    return user
