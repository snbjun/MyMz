from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.modules.users.model import User
from app.modules.users.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """骨架阶段新增：统一数据库会话依赖，业务路由后续复用。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """第 2 阶段新增：从 Bearer Token 解析当前登录用户。"""

    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证已失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise auth_error

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(str(payload.get("sub")))
    except (ValueError, TypeError):
        raise auth_error from None

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise auth_error
    return user


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """第 2 阶段新增：用户管理接口暂时只允许超级管理员访问。"""

    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理用户")
    return current_user
