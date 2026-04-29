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
from app.modules.inventory.model import Inventory, StockMovement, Warehouse
from app.modules.products.model import Product, ProductCategory, ProductUnit


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 6 阶段新增：库存测试使用临时 SQLite，避免污染 data/app.db。"""

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
        db.add(Warehouse(name="默认仓库", sort_order=0, is_default=True, is_active=True))
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


def create_category(client: TestClient, token: str, name: str = "库存分类") -> dict:
    response = client.post("/api/product-categories", headers=auth_headers(token), json={"name": name})
    assert response.status_code == 200
    return dict(response.json())


def create_product(
    client: TestClient,
    token: str,
    name: str = "库存产品",
    code: str | None = None,
    category_id: int | None = None,
    warning_qty: str = "0.000",
    purchase_price: str = "8.0000",
) -> dict:
    response = client.post(
        "/api/products",
        headers=auth_headers(token),
        json={
            "code": code or f"INV-{name}",
            "barcode": f"BAR-{name}",
            "name": name,
            "category_id": category_id,
            "spec": "标准规格",
            "model": "M1",
            "brand": "测试品牌",
            "sale_price": "12.00",
            "purchase_price": purchase_price,
            "wholesale_price": "10.00",
            "stock_warning_qty": warning_qty,
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def movement_count(client: TestClient, token: str, product_id: int | None = None) -> int:
    url = "/api/stock-movements"
    if product_id is not None:
        url += f"?product_id={product_id}"
    response = client.get(url, headers=auth_headers(token))
    assert response.status_code == 200
    return int(response.json()["total"])


def set_initial(client: TestClient, token: str, product_id: int, quantity: str = "10.000", unit_cost: str = "2.5000") -> dict:
    response = client.post(
        "/api/inventory/initial-stock",
        headers=auth_headers(token),
        json={"product_id": product_id, "quantity": quantity, "unit_cost": unit_cost, "remark": "期初"},
    )
    assert response.status_code == 200
    return dict(response.json())


def adjust(client: TestClient, token: str, payload: dict) -> dict:
    response = client.post("/api/inventory/adjustments", headers=auth_headers(token), json=payload)
    assert response.status_code == 200
    return dict(response.json())


def test_anonymous_user_cannot_access_inventory_list(client: TestClient) -> None:
    response = client.get("/api/inventory")
    assert response.status_code == 401


def test_default_warehouse_can_be_queried(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/warehouses", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "默认仓库"
    assert data[0]["is_default"] is True


def test_product_without_inventory_is_visible_as_zero_stock(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "零库存产品")
    response = client.get("/api/inventory", headers=auth_headers(token))
    assert response.status_code == 200
    item = next(item for item in response.json()["items"] if item["product_id"] == product["id"])
    assert item["quantity_on_hand"] == "0.000"
    assert item["average_cost"] == "0.0000"
    assert item["total_cost"] == "0.00"


def test_can_set_initial_stock(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "期初产品")
    inventory = set_initial(client, token, product["id"], "5.000", "3.2000")
    assert inventory["quantity_on_hand"] == "5.000"
    assert inventory["average_cost"] == "3.2000"
    assert inventory["total_cost"] == "16.00"


def test_initial_stock_creates_inventory_balance(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "期初余额产品")
    set_initial(client, token, product["id"], "7.000", "2.0000")
    response = client.get(f"/api/inventory/{product['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == "7.000"


def test_positive_initial_stock_creates_stock_movement(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "期初流水产品")
    assert movement_count(client, token, product["id"]) == 0
    set_initial(client, token, product["id"], "1.500", "4.0000")
    response = client.get("/api/stock-movements?movement_type=initial", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["quantity"] == "1.500"


def test_initial_stock_cannot_be_set_twice_after_movement_exists(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "重复期初产品")
    set_initial(client, token, product["id"], "2.000", "2.0000")
    response = client.post(
        "/api/inventory/initial-stock",
        headers=auth_headers(token),
        json={"product_id": product["id"], "quantity": "1.000", "unit_cost": "1.0000"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "该产品已有库存流水，不能重复设置期初库存"


def test_increase_adjustment_adds_stock_and_creates_in_movement(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "增加调整产品")
    inventory = adjust(client, token, {"product_id": product["id"], "mode": "increase", "quantity": "3.000", "unit_cost": "5.0000"})
    assert inventory["quantity_on_hand"] == "3.000"
    response = client.get("/api/stock-movements?movement_type=adjustment_in", headers=auth_headers(token))
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["direction"] == "in"


def test_decrease_adjustment_reduces_stock_and_creates_out_movement(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "减少调整产品")
    set_initial(client, token, product["id"], "5.000", "2.0000")
    inventory = adjust(client, token, {"product_id": product["id"], "mode": "decrease", "quantity": "2.000"})
    assert inventory["quantity_on_hand"] == "3.000"
    response = client.get("/api/stock-movements?movement_type=adjustment_out", headers=auth_headers(token))
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["direction"] == "out"


def test_decrease_cannot_make_negative_stock(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "负库存产品")
    set_initial(client, token, product["id"], "1.000", "2.0000")
    response = client.post(
        "/api/inventory/adjustments",
        headers=auth_headers(token),
        json={"product_id": product["id"], "mode": "decrease", "quantity": "2.000"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "库存不足，调整后库存不能为负数"


def test_set_higher_stock_creates_stocktaking_gain(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "盘盈产品")
    set_initial(client, token, product["id"], "2.000", "1.0000")
    inventory = adjust(client, token, {"product_id": product["id"], "mode": "set", "target_qty": "5.000", "unit_cost": "3.0000"})
    assert inventory["quantity_on_hand"] == "5.000"
    response = client.get("/api/stock-movements?movement_type=stocktaking_gain", headers=auth_headers(token))
    assert response.json()["total"] == 1


def test_set_lower_stock_creates_stocktaking_loss(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "盘亏产品")
    set_initial(client, token, product["id"], "5.000", "1.0000")
    inventory = adjust(client, token, {"product_id": product["id"], "mode": "set", "target_qty": "2.000"})
    assert inventory["quantity_on_hand"] == "2.000"
    response = client.get("/api/stock-movements?movement_type=stocktaking_loss", headers=auth_headers(token))
    assert response.json()["total"] == 1


def test_set_same_stock_does_not_create_movement(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "无差异盘点产品")
    set_initial(client, token, product["id"], "5.000", "1.0000")
    before_count = movement_count(client, token, product["id"])
    inventory = adjust(client, token, {"product_id": product["id"], "mode": "set", "target_qty": "5.000"})
    after_count = movement_count(client, token, product["id"])
    assert inventory["quantity_on_hand"] == "5.000"
    assert after_count == before_count


def test_inbound_adjustment_recalculates_moving_weighted_average_cost(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "加权成本产品")
    set_initial(client, token, product["id"], "10.000", "2.0000")
    inventory = adjust(client, token, {"product_id": product["id"], "mode": "increase", "quantity": "10.000", "unit_cost": "4.0000"})
    assert inventory["quantity_on_hand"] == "20.000"
    assert inventory["average_cost"] == "3.0000"
    assert inventory["total_cost"] == "60.00"


def test_outbound_adjustment_amount_uses_current_average_cost(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "出库成本产品")
    set_initial(client, token, product["id"], "10.000", "2.5000")
    adjust(client, token, {"product_id": product["id"], "mode": "decrease", "quantity": "4.000"})
    response = client.get("/api/stock-movements?movement_type=adjustment_out", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["unit_cost"] == "2.5000"
    assert item["amount"] == "10.00"


def test_inventory_list_supports_pagination(client: TestClient) -> None:
    token = login(client)
    for index in range(3):
        create_product(client, token, f"库存分页产品{index}")
    response = client.get("/api/inventory?page=1&page_size=2", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2


def test_inventory_list_supports_keyword_search(client: TestClient) -> None:
    token = login(client)
    create_product(client, token, "库存搜索产品A", code="SEARCH-A")
    create_product(client, token, "库存普通产品B", code="NORMAL-B")
    response = client.get("/api/inventory?keyword=SEARCH", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["product_code"] == "SEARCH-A"


def test_inventory_list_supports_category_filter(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "库存筛选分类")
    create_product(client, token, "库存分类产品", category_id=category["id"])
    create_product(client, token, "库存无分类产品")
    response = client.get(f"/api/inventory?category_id={category['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["product_name"] == "库存分类产品"


def test_inventory_list_supports_low_stock_filter(client: TestClient) -> None:
    token = login(client)
    low_product = create_product(client, token, "低库存产品", warning_qty="5.000")
    normal_product = create_product(client, token, "正常库存产品", warning_qty="5.000")
    set_initial(client, token, normal_product["id"], "10.000", "1.0000")
    response = client.get("/api/inventory?low_stock_only=true", headers=auth_headers(token))
    assert response.status_code == 200
    names = [item["product_name"] for item in response.json()["items"]]
    assert "低库存产品" in names
    assert "正常库存产品" not in names
    assert response.json()["items"][0]["is_low_stock"] is True
    assert low_product["stock_warning_qty"] == "5.000"


def test_stock_movement_list_supports_pagination(client: TestClient) -> None:
    token = login(client)
    for index in range(3):
        product = create_product(client, token, f"流水分页产品{index}")
        set_initial(client, token, product["id"], "1.000", "1.0000")
    response = client.get("/api/stock-movements?page=1&page_size=2", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2


def test_stock_movement_list_supports_product_filter(client: TestClient) -> None:
    token = login(client)
    product_a = create_product(client, token, "流水产品A")
    product_b = create_product(client, token, "流水产品B")
    set_initial(client, token, product_a["id"], "1.000", "1.0000")
    set_initial(client, token, product_b["id"], "1.000", "1.0000")
    response = client.get(f"/api/stock-movements?product_id={product_a['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["product_id"] == product_a["id"]


def test_stock_movement_list_supports_type_filter(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "流水类型产品")
    set_initial(client, token, product["id"], "1.000", "1.0000")
    adjust(client, token, {"product_id": product["id"], "mode": "increase", "quantity": "1.000", "unit_cost": "2.0000"})
    response = client.get("/api/stock-movements?movement_type=adjustment_in", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["movement_type"] == "adjustment_in"


def test_quantity_fields_use_numeric_and_serialize_safely(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "库存数量字段")
    inventory = set_initial(client, token, product["id"], "1.235", "2.0000")
    columns = inspect(Inventory).columns
    movement_columns = inspect(StockMovement).columns
    assert isinstance(columns.quantity_on_hand.type, Numeric)
    assert columns.quantity_on_hand.type.scale == 3
    assert isinstance(movement_columns.quantity.type, Numeric)
    assert inventory["quantity_on_hand"] == "1.235"
    assert Decimal(inventory["quantity_on_hand"]) == Decimal("1.235")


def test_money_and_cost_fields_use_numeric_and_serialize_safely(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "库存金额字段")
    inventory = set_initial(client, token, product["id"], "2.000", "3.4567")
    columns = inspect(Inventory).columns
    movement_columns = inspect(StockMovement).columns
    assert isinstance(columns.average_cost.type, Numeric)
    assert isinstance(columns.total_cost.type, Numeric)
    assert isinstance(movement_columns.unit_cost.type, Numeric)
    assert isinstance(movement_columns.amount.type, Numeric)
    assert inventory["average_cost"] == "3.4567"
    assert inventory["total_cost"] == "6.91"


def test_inventory_writes_do_not_skip_stock_movements(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token, "流水保护产品")
    before = movement_count(client, token, product["id"])
    adjust(client, token, {"product_id": product["id"], "mode": "increase", "quantity": "2.000", "unit_cost": "1.0000"})
    middle = movement_count(client, token, product["id"])
    adjust(client, token, {"product_id": product["id"], "mode": "decrease", "quantity": "1.000"})
    after = movement_count(client, token, product["id"])
    assert middle == before + 1
    assert after == middle + 1
