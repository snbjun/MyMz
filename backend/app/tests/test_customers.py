from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Numeric, create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.deps import get_db
from app.main import create_app
from app.modules.auth.service import init_admin_user
from app.modules.customers.model import Customer, CustomerCategory


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 3 阶段新增：客户测试使用临时 SQLite，避免污染 data/app.db。"""

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
        db.add(CustomerCategory(name="默认分类", sort_order=0, is_default=True))
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def login(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123456"})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_category(client: TestClient, token: str, name: str = "重点客户") -> dict:
    response = client.post(
        "/api/customer-categories",
        headers=auth_headers(token),
        json={"name": name, "sort_order": 10},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_customer(
    client: TestClient,
    token: str,
    name: str = "华东客户",
    category_id: int | None = None,
    phone: str = "13800000000",
    address: str = "上海市",
) -> dict:
    response = client.post(
        "/api/customers",
        headers=auth_headers(token),
        json={
            "code": f"C-{name}",
            "name": name,
            "category_id": category_id,
            "contact_name": "张三",
            "phone": phone,
            "address": address,
            "opening_receivable": "12.34",
            "credit_limit": "1000.00",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def test_anonymous_user_cannot_access_customer_list(client: TestClient) -> None:
    response = client.get("/api/customers")
    assert response.status_code == 401


def test_logged_in_user_can_create_customer_category(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token)
    assert category["name"] == "重点客户"


def test_duplicate_active_category_name_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_category(client, token, "重复分类")
    response = client.post(
        "/api/customer-categories",
        headers=auth_headers(token),
        json={"name": "重复分类"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "客户分类名称已存在"


def test_can_create_customer(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token)
    customer = create_customer(client, token, category_id=category["id"])
    assert customer["name"] == "华东客户"
    assert customer["category_name"] == "重点客户"
    assert customer["current_receivable"] == "12.34"


def test_customer_name_is_required(client: TestClient) -> None:
    token = login(client)
    response = client.post(
        "/api/customers",
        headers=auth_headers(token),
        json={"name": "", "opening_receivable": "0.00", "current_receivable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 422


def test_duplicate_active_customer_name_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_customer(client, token, "重复客户")
    response = client.post(
        "/api/customers",
        headers=auth_headers(token),
        json={"name": "重复客户", "opening_receivable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "客户名称已存在"


def test_customer_list_supports_pagination(client: TestClient) -> None:
    token = login(client)
    for index in range(3):
        create_customer(client, token, f"分页客户{index}")
    response = client.get("/api/customers?page=1&page_size=2", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_customer_list_supports_keyword_search(client: TestClient) -> None:
    token = login(client)
    create_customer(client, token, "搜索客户A", phone="13911112222", address="杭州市")
    create_customer(client, token, "普通客户B", phone="13933334444", address="苏州市")
    response = client.get("/api/customers?keyword=杭州", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "搜索客户A"


def test_customer_list_supports_category_filter(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "分类筛选")
    create_customer(client, token, "分类客户", category_id=category["id"])
    create_customer(client, token, "无分类客户")
    response = client.get(f"/api/customers?category_id={category['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "分类客户"


def test_can_update_customer(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token, "待编辑客户")
    response = client.put(
        f"/api/customers/{customer['id']}",
        headers=auth_headers(token),
        json={"name": "已编辑客户", "phone": "021-88888888", "current_receivable": "20.00"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "已编辑客户"
    assert response.json()["current_receivable"] == "20.00"


def test_delete_customer_is_soft_delete(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token, "待删除客户")
    response = client.delete(f"/api/customers/{customer['id']}", headers=auth_headers(token))
    assert response.status_code == 200

    get_response = client.get(f"/api/customers/{customer['id']}", headers=auth_headers(token))
    assert get_response.status_code == 404


def test_deleted_customer_is_not_returned_in_list(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token, "列表删除客户")
    client.delete(f"/api/customers/{customer['id']}", headers=auth_headers(token))
    response = client.get("/api/customers?keyword=列表删除客户", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_cannot_delete_category_used_by_customer(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "已使用分类")
    create_customer(client, token, "分类占用客户", category_id=category["id"])
    response = client.delete(f"/api/customer-categories/{category['id']}", headers=auth_headers(token))
    assert response.status_code == 400
    assert response.json()["detail"] == "分类正在被客户使用，不能删除"


def test_can_toggle_customer_active(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token, "启停客户")
    response = client.post(f"/api/customers/{customer['id']}/toggle-active", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_money_fields_use_numeric_and_serialize_as_strings(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token, "金额客户")
    columns = inspect(Customer).columns
    assert isinstance(columns.opening_receivable.type, Numeric)
    assert isinstance(columns.current_receivable.type, Numeric)
    assert isinstance(columns.credit_limit.type, Numeric)
    assert customer["opening_receivable"] == "12.34"
    assert customer["current_receivable"] == "12.34"
    assert customer["credit_limit"] == "1000.00"
    assert Decimal(customer["opening_receivable"]) == Decimal("12.34")
