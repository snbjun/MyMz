from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """骨架阶段新增：统一数据库会话依赖，业务路由后续复用。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
