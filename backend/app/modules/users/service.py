from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import PasswordReset, UserCreate, UserListResponse, UserUpdate


class UserService:
    """第 2 阶段新增：用户管理业务规则集中在 service 层。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def list_users(self, keyword: str | None, page: int, page_size: int) -> UserListResponse:
        items, total = self.repo.list_users(keyword, page, page_size)
        return UserListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_user(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return user

    def create_user(self, payload: UserCreate) -> User:
        if self.repo.get_by_username(payload.username, include_deleted=True) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

        user = User(
            username=payload.username,
            display_name=payload.display_name,
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
            is_superuser=payload.is_superuser,
        )
        self.repo.create(user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在") from None
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        self._ensure_last_superuser_remains(
            user,
            next_is_active=payload.is_active,
            next_is_superuser=payload.is_superuser,
        )

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def reset_password(self, user_id: int, payload: PasswordReset) -> None:
        user = self.get_user(user_id)
        user.password_hash = hash_password(payload.password)
        self.db.commit()

    def delete_user(self, user_id: int, current_user: User) -> None:
        user = self.get_user(user_id)
        if user.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录用户")
        self._ensure_last_superuser_remains(user, next_is_active=False, next_is_superuser=False)
        self.repo.soft_delete(user)
        self.db.commit()

    def toggle_active(self, user_id: int, current_user: User) -> User:
        user = self.get_user(user_id)
        if user.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用当前登录用户")
        next_active = not user.is_active
        self._ensure_last_superuser_remains(user, next_is_active=next_active, next_is_superuser=None)
        user.is_active = next_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def _ensure_last_superuser_remains(
        self,
        user: User,
        next_is_active: bool | None,
        next_is_superuser: bool | None,
    ) -> None:
        if not user.is_superuser or not user.is_active:
            return

        will_still_be_superuser = user.is_superuser if next_is_superuser is None else next_is_superuser
        will_still_be_active = user.is_active if next_is_active is None else next_is_active
        if will_still_be_superuser and will_still_be_active:
            return

        if self.repo.count_active_superusers(exclude_user_id=user.id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除或禁用最后一个超级管理员",
            )
