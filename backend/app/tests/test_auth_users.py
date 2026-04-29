from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.deps import get_db
from app.main import create_app
from app.modules.auth.service import init_admin_user
from app.modules.users.model import User


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 2 阶段新增：每个测试使用临时 SQLite，避免污染 data/app.db。"""

    database_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestingSessionLocal() as db:
        init_admin_user(db, username="admin", password="admin123456", display_name="系统管理员")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def login(client: TestClient, username: str = "admin", password: str = "admin123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_check_still_passes(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_initialized_admin_can_login(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_superuser"] is True


def test_wrong_password_cannot_login(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "bad-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_logged_in_user_can_access_me(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_anonymous_user_cannot_access_me(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_superuser_can_create_user(client: TestClient) -> None:
    token = login(client)
    response = client.post(
        "/api/users",
        headers=auth_headers(token),
        json={
            "username": "staff01",
            "display_name": "普通员工",
            "password": "staff123456",
            "role": "staff",
            "is_active": True,
            "is_superuser": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "staff01"
    assert "password_hash" not in data


def test_normal_user_cannot_create_user(client: TestClient) -> None:
    admin_token = login(client)
    client.post(
        "/api/users",
        headers=auth_headers(admin_token),
        json={
            "username": "staff02",
            "display_name": "普通员工二",
            "password": "staff123456",
            "role": "staff",
            "is_active": True,
            "is_superuser": False,
        },
    )

    staff_token = login(client, "staff02", "staff123456")
    response = client.post(
        "/api/users",
        headers=auth_headers(staff_token),
        json={"username": "blocked", "display_name": "无权限", "password": "staff123456"},
    )
    assert response.status_code == 403


def test_delete_user_is_soft_delete(client: TestClient) -> None:
    token = login(client)
    create_response = client.post(
        "/api/users",
        headers=auth_headers(token),
        json={"username": "staff03", "display_name": "待删除", "password": "staff123456"},
    )
    user_id = create_response.json()["id"]

    response = client.delete(f"/api/users/{user_id}", headers=auth_headers(token))
    assert response.status_code == 200

    deleted_response = client.get(f"/api/users/{user_id}", headers=auth_headers(token))
    assert deleted_response.status_code == 404


def test_cannot_delete_self(client: TestClient) -> None:
    token = login(client)
    me_response = client.get("/api/auth/me", headers=auth_headers(token))
    response = client.delete(f"/api/users/{me_response.json()['id']}", headers=auth_headers(token))
    assert response.status_code == 400
    assert response.json()["detail"] == "不能删除当前登录用户"


def test_cannot_disable_last_superuser(client: TestClient) -> None:
    token = login(client)
    me_response = client.get("/api/auth/me", headers=auth_headers(token))
    response = client.put(
        f"/api/users/{me_response.json()['id']}",
        headers=auth_headers(token),
        json={"is_active": False},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "不能删除或禁用最后一个超级管理员"
