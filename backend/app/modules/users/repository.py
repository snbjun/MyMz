from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.users.model import User


class UserRepository:
    """第 2 阶段新增：封装用户数据访问，避免 router 直接操作数据库。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int, include_deleted: bool = False) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_username(self, username: str, include_deleted: bool = False) -> User | None:
        stmt = select(User).where(User.username == username)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def list_users(self, keyword: str | None, page: int, page_size: int) -> tuple[list[User], int]:
        filters = [User.deleted_at.is_(None)]
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(or_(User.username.like(like_keyword), User.display_name.like(like_keyword)))

        count_stmt = select(func.count()).select_from(User).where(and_(*filters))
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = (
            select(User)
            .where(and_(*filters))
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def count_active_superusers(self, exclude_user_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(User).where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            User.is_superuser.is_(True),
        )
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        return int(self.db.scalar(stmt) or 0)

    def create(self, user: User) -> User:
        self.db.add(user)
        return user

    def soft_delete(self, user: User) -> User:
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        return user
