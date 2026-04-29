from app.core.database import SessionLocal
from app.modules.auth.service import init_admin_user


def main() -> None:
    """第 2 阶段新增：初始化默认管理员账号，可重复执行。"""

    db = SessionLocal()
    try:
        init_admin_user(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
