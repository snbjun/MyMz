from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import LoginRequest, LoginResponse
from app.modules.audit_logs.service import record_audit_log
from app.modules.users.model import User
from app.modules.users.repository import UserRepository


class AuthService:
    """第 2 阶段新增：认证业务从前端静态跳转改为后端 JWT 登录。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def login(self, payload: LoginRequest, request: Request | None = None) -> LoginResponse:
        user = self.repo.get_by_username(payload.username)
        if (
            user is None
            or not user.is_active
            or not verify_password(payload.password, user.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        record_audit_log(
            self.db,
            user,
            module="auth",
            action="login",
            target_type="user",
            target_id=user.id,
            target_label=user.username,
            summary=f"登录成功：{user.username}",
            request=request,
        )
        return LoginResponse(access_token=create_access_token(str(user.id)), user=user)


def init_admin_user(
    db: Session,
    username: str | None = None,
    password: str | None = None,
    display_name: str | None = None,
) -> User:
    """第 2 阶段新增：可重复执行的默认管理员初始化逻辑。"""

    repo = UserRepository(db)
    admin_username = username or settings.admin_username
    existing = repo.get_by_username(admin_username, include_deleted=True)
    if existing is not None:
        return existing

    admin = User(
        username=admin_username,
        display_name=display_name or settings.admin_display_name,
        password_hash=hash_password(password or settings.admin_password),
        role="admin",
        is_active=True,
        is_superuser=True,
    )
    repo.create(admin)
    db.commit()
    db.refresh(admin)
    return admin
