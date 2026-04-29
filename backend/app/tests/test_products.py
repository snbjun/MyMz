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
from app.modules.products.model import Product, ProductCategory, ProductUnit


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 5 阶段新增：产品测试使用临时 SQLite，避免污染 data/app.db。"""

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
        db.add(ProductCategory(name="默认分类", sort_order=0, is_default=True))
        db.add(ProductUnit(name="个", sort_order=0, is_default=True))
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


def create_category(client: TestClient, token: str, name: str = "成品") -> dict:
    response = client.post(
        "/api/product-categories",
        headers=auth_headers(token),
        json={"name": name, "sort_order": 10},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_unit(client: TestClient, token: str, name: str = "箱") -> dict:
    response = client.post(
        "/api/product-units",
        headers=auth_headers(token),
        json={"name": name, "sort_order": 10},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_product(
    client: TestClient,
    token: str,
    name: str = "标准产品",
    code: str | None = None,
    barcode: str | None = None,
    category_id: int | None = None,
    unit_id: int | None = None,
    brand: str = "自有品牌",
) -> dict:
    response = client.post(
        "/api/products",
        headers=auth_headers(token),
        json={
            "code": code or f"P-{name}",
            "barcode": barcode or f"B-{name}",
            "name": name,
            "category_id": category_id,
            "unit_id": unit_id,
            "spec": "标准规格",
            "model": "M1",
            "brand": brand,
            "origin": "中国",
            "sale_price": "12.34",
            "purchase_price": "8.50",
            "wholesale_price": "10.00",
            "stock_warning_qty": "3.125",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def test_anonymous_user_cannot_access_product_list(client: TestClient) -> None:
    response = client.get("/api/products")
    assert response.status_code == 401


def test_logged_in_user_can_create_product_category(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token)
    assert category["name"] == "成品"


def test_duplicate_active_category_name_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_category(client, token, "重复分类")
    response = client.post("/api/product-categories", headers=auth_headers(token), json={"name": "重复分类"})
    assert response.status_code == 400
    assert response.json()["detail"] == "产品分类名称已存在"


def test_cannot_delete_category_used_by_product(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "已使用分类")
    create_product(client, token, "分类占用产品", category_id=category["id"])
    response = client.delete(f"/api/product-categories/{category['id']}", headers=auth_headers(token))
    assert response.status_code == 400
    assert response.json()["detail"] == "分类正在被产品使用，不能删除"


def test_logged_in_user_can_create_product_unit(client: TestClient) -> None:
    token = login(client)
    unit = create_unit(client, token)
    assert unit["name"] == "箱"


def test_duplicate_active_unit_name_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_unit(client, token, "包")
    response = client.post("/api/product-units", headers=auth_headers(token), json={"name": "包"})
    assert response.status_code == 400
    assert response.json()["detail"] == "产品单位名称已存在"


def test_cannot_delete_unit_used_by_product(client: TestClient) -> None:
    token = login(client)
    unit = create_unit(client, token, "套")
    create_product(client, token, "单位占用产品", unit_id=unit["id"])
    response = client.delete(f"/api/product-units/{unit['id']}", headers=auth_headers(token))
    assert response.status_code == 400
    assert response.json()["detail"] == "单位正在被产品使用，不能删除"


def test_can_create_product(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token)
    unit = create_unit(client, token)
    product = create_product(client, token, category_id=category["id"], unit_id=unit["id"])
    assert product["name"] == "标准产品"
    assert product["category_name"] == "成品"
    assert product["unit_name"] == "箱"


def test_product_name_is_required(client: TestClient) -> None:
    token = login(client)
    response = client.post("/api/products", headers=auth_headers(token), json={"name": ""})
    assert response.status_code == 422


def test_duplicate_active_product_name_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_product(client, token, "重复产品")
    response = client.post("/api/products", headers=auth_headers(token), json={"name": "重复产品"})
    assert response.status_code == 400
    assert response.json()["detail"] == "产品名称已存在"


def test_duplicate_non_empty_product_code_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_product(client, token, "编号产品A", code="P001")
    response = client.post("/api/products", headers=auth_headers(token), json={"name": "编号产品B", "code": "P001"})
    assert response.status_code == 400
    assert response.json()["detail"] == "产品编号已存在"


def test_duplicate_non_empty_barcode_is_rejected(client: TestClient) -> None:
    token = login(client)
    create_product(client, token, "条码产品A", barcode="BAR001")
    response = client.post("/api/products", headers=auth_headers(token), json={"name": "条码产品B", "barcode": "BAR001"})
    assert response.status_code == 400
    assert response.json()["detail"] == "产品条码已存在"


def test_product_list_supports_pagination(client: TestClient) -> None:
    token = login(client)
    for index in range(3):
        create_product(client, token, f"分页产品{index}")
    response = client.get("/api/products?page=1&page_size=2", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_product_list_supports_keyword_search(client: TestClient) -> None:
    token = login(client)
    create_product(client, token, "搜索产品A", brand="杭州品牌")
    create_product(client, token, "普通产品B", brand="苏州品牌")
    response = client.get("/api/products?keyword=杭州", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "搜索产品A"


def test_product_list_supports_category_filter(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "分类筛选")
    create_product(client, token, "分类产品", category_id=category["id"])
    create_product(client, token, "无分类产品")
    response = client.get(f"/api/products?category_id={category['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "分类产品"


def test_product_list_supports_unit_filter(client: TestClient) -> None:
    token = login(client)
    unit = create_unit(client, token, "筛选单位")
    create_product(client, token, "单位产品", unit_id=unit["id"])
    create_product(client, token, "无单位产品")
    response = client.get(f"/api/products?unit_id={unit['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "单位产品"


def test_can_update_product(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "待编辑产品")
    response = client.put(
        f"/api/products/{product['id']}",
        headers=auth_headers(token),
        json={"name": "已编辑产品", "sale_price": "20.00", "stock_warning_qty": "6.500"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "已编辑产品"
    assert response.json()["sale_price"] == "20.00"
    assert response.json()["stock_warning_qty"] == "6.500"


def test_delete_product_is_soft_delete(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "待删除产品")
    response = client.delete(f"/api/products/{product['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    get_response = client.get(f"/api/products/{product['id']}", headers=auth_headers(token))
    assert get_response.status_code == 404


def test_deleted_product_is_not_returned_in_list(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "列表删除产品")
    client.delete(f"/api/products/{product['id']}", headers=auth_headers(token))
    response = client.get("/api/products?keyword=列表删除产品", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_can_toggle_product_active(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "启停产品")
    response = client.post(f"/api/products/{product['id']}/toggle-active", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_money_fields_use_numeric_and_serialize_as_strings(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "金额产品")
    columns = inspect(Product).columns
    assert isinstance(columns.sale_price.type, Numeric)
    assert isinstance(columns.purchase_price.type, Numeric)
    assert isinstance(columns.wholesale_price.type, Numeric)
    assert product["sale_price"] == "12.34"
    assert product["purchase_price"] == "8.50"
    assert product["wholesale_price"] == "10.00"
    assert Decimal(product["sale_price"]) == Decimal("12.34")


def test_quantity_field_uses_numeric_and_serializes_as_string(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "数量产品")
    columns = inspect(Product).columns
    assert isinstance(columns.stock_warning_qty.type, Numeric)
    assert columns.stock_warning_qty.type.scale == 3
    assert product["stock_warning_qty"] == "3.125"
    assert Decimal(product["stock_warning_qty"]) == Decimal("3.125")
