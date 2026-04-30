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
from app.modules.suppliers.model import Supplier, SupplierCategory
from app.modules.inventory.model import Warehouse
from app.modules.products.model import Product, ProductCategory, ProductUnit
from app.modules.purchase.model import PurchaseOrder, PurchaseOrderItem


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 8 阶段新增：采购单测试使用临时 SQLite，避免污染 data/app.db。"""

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
        db.add(SupplierCategory(name="默认分类", sort_order=0, is_default=True))
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


def create_supplier(client: TestClient, token: str, name: str = "采购供应商") -> dict:
    response = client.post(
        "/api/suppliers",
        headers=auth_headers(token),
        json={"name": name, "opening_payable": "0.00", "current_payable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_product(client: TestClient, token: str, name: str = "采购产品", purchase_price: str = "10.00") -> dict:
    response = client.post(
        "/api/products",
        headers=auth_headers(token),
        json={
            "code": f"P-{name}",
            "barcode": f"PB-{name}",
            "name": name,
            "spec": "标准规格",
            "model": "M1",
            "sale_price": "12.00",
            "purchase_price": purchase_price,
            "wholesale_price": "8.00",
            "stock_warning_qty": "0.000",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_order(client: TestClient, token: str, supplier_id: int, product_id: int, quantity: str = "2.000") -> dict:
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={
            "supplier_id": supplier_id,
            "order_date": "2026-04-30",
            "discount_amount": "0.00",
            "remark": "采购测试",
            "items": [{"product_id": product_id, "quantity": quantity, "unit_price": "10.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_basic_order(client: TestClient, token: str, quantity: str = "2.000") -> tuple[dict, dict, dict]:
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    order = create_order(client, token, supplier["id"], product["id"], quantity)
    return supplier, product, order


def confirm_order(client: TestClient, token: str, order_id: int) -> dict:
    response = client.post(f"/api/purchase-orders/{order_id}/confirm", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json())


def set_initial_stock(client: TestClient, token: str, product_id: int, quantity: str = "10.000") -> None:
    response = client.post(
        "/api/inventory/initial-stock",
        headers=auth_headers(token),
        json={"product_id": product_id, "quantity": quantity, "unit_cost": "5.0000"},
    )
    assert response.status_code == 200


def get_supplier(client: TestClient, token: str, supplier_id: int) -> dict:
    response = client.get(f"/api/suppliers/{supplier_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json())


def get_inventory(client: TestClient, token: str, product_id: int) -> dict:
    response = client.get(f"/api/inventory/{product_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json())


def test_anonymous_user_cannot_access_purchase_order_list(client: TestClient) -> None:
    response = client.get("/api/purchase-orders")
    assert response.status_code == 401


def test_can_create_draft_purchase_order(client: TestClient) -> None:
    token = login(client)
    supplier, product, order = create_basic_order(client, token)
    assert order["status"] == "draft"
    assert order["supplier_id"] == supplier["id"]
    assert order["items"][0]["product_id"] == product["id"]


def test_purchase_order_requires_at_least_one_item(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    response = client.post("/api/purchase-orders", headers=auth_headers(token), json={"supplier_id": supplier["id"], "items": []})
    assert response.status_code == 422


def test_supplier_missing_or_disabled_cannot_create_purchase_order(client: TestClient) -> None:
    token = login(client)
    product = create_product(client, token)
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={"supplier_id": 999, "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "1.00"}]},
    )
    assert response.status_code == 400
    supplier = create_supplier(client, token, "禁用供应商")
    client.post(f"/api/suppliers/{supplier['id']}/toggle-active", headers=auth_headers(token))
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "1.00"}]},
    )
    assert response.status_code == 400


def test_product_missing_or_disabled_cannot_create_purchase_order(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": 999, "quantity": "1.000", "unit_price": "1.00"}]},
    )
    assert response.status_code == 400
    product = create_product(client, token, "禁用产品")
    client.post(f"/api/products/{product['id']}/toggle-active", headers=auth_headers(token))
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "1.00"}]},
    )
    assert response.status_code == 400


def test_quantity_must_be_positive(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "0.000", "unit_price": "1.00"}]},
    )
    assert response.status_code == 422


def test_unit_price_cannot_be_negative(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "-1.00"}]},
    )
    assert response.status_code == 422


def test_draft_order_does_not_affect_inventory(client: TestClient) -> None:
    token = login(client)
    _, product, _ = create_basic_order(client, token)
    assert get_inventory(client, token, product["id"])["quantity_on_hand"] == "0.000"


def test_draft_order_does_not_affect_supplier_payable(client: TestClient) -> None:
    token = login(client)
    supplier, _, _ = create_basic_order(client, token)
    assert get_supplier(client, token, supplier["id"])["current_payable"] == "0.00"


def test_only_draft_order_can_be_edited(client: TestClient) -> None:
    token = login(client)
    supplier, product, order = create_basic_order(client, token)
    response = client.put(
        f"/api/purchase-orders/{order['id']}",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "3.000", "unit_price": "9.00"}]},
    )
    assert response.status_code == 200
    confirm_order(client, token, order["id"])
    response = client.put(
        f"/api/purchase-orders/{order['id']}",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "9.00"}]},
    )
    assert response.status_code == 400


def test_confirm_order_increases_supplier_payable(client: TestClient) -> None:
    token = login(client)
    supplier, _, order = create_basic_order(client, token)
    confirmed = confirm_order(client, token, order["id"])
    assert confirmed["status"] == "confirmed"
    assert get_supplier(client, token, supplier["id"])["current_payable"] == "20.00"


def test_confirm_order_does_not_increase_inventory(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    set_initial_stock(client, token, product["id"], "5.000")
    confirm_order(client, token, order["id"])
    assert get_inventory(client, token, product["id"])["quantity_on_hand"] == "5.000"


def test_confirm_order_twice_fails(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    response = client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=auth_headers(token))
    assert response.status_code == 400


def test_confirmed_order_cannot_be_edited(client: TestClient) -> None:
    token = login(client)
    supplier, product, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    response = client.put(
        f"/api/purchase-orders/{order['id']}",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "8.00"}]},
    )
    assert response.status_code == 400


def test_receiving_increases_inventory(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    set_initial_stock(client, token, product["id"], "10.000")
    confirmed = confirm_order(client, token, order["id"])
    item_id = confirmed["items"][0]["id"]
    response = client.post(
        f"/api/purchase-orders/{order['id']}/receive",
        headers=auth_headers(token),
        json={"items": [{"item_id": item_id, "quantity": "2.000"}]},
    )
    assert response.status_code == 200
    assert get_inventory(client, token, product["id"])["quantity_on_hand"] == "12.000"


def test_receiving_creates_purchase_in_stock_movement(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    set_initial_stock(client, token, product["id"], "10.000")
    confirmed = confirm_order(client, token, order["id"])
    item_id = confirmed["items"][0]["id"]
    client.post(f"/api/purchase-orders/{order['id']}/receive", headers=auth_headers(token), json={"items": [{"item_id": item_id, "quantity": "1.000"}]})
    response = client.get("/api/stock-movements?movement_type=purchase_in", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["source_type"] == "purchase_order"


def test_receiving_can_create_inventory_from_zero(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    confirmed = confirm_order(client, token, order["id"])
    response = client.post(
        f"/api/purchase-orders/{order['id']}/receive",
        headers=auth_headers(token),
        json={"items": [{"item_id": confirmed["items"][0]["id"], "quantity": "1.000"}]},
    )
    assert response.status_code == 200
    assert get_inventory(client, token, product["id"])["quantity_on_hand"] == "1.000"


def test_receiving_quantity_cannot_exceed_unreceived_quantity(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    set_initial_stock(client, token, product["id"], "10.000")
    confirmed = confirm_order(client, token, order["id"])
    response = client.post(
        f"/api/purchase-orders/{order['id']}/receive",
        headers=auth_headers(token),
        json={"items": [{"item_id": confirmed["items"][0]["id"], "quantity": "3.000"}]},
    )
    assert response.status_code == 400


def test_partial_receiving_sets_partial_received_status(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token, "3.000")
    set_initial_stock(client, token, product["id"], "10.000")
    confirmed = confirm_order(client, token, order["id"])
    response = client.post(
        f"/api/purchase-orders/{order['id']}/receive",
        headers=auth_headers(token),
        json={"items": [{"item_id": confirmed["items"][0]["id"], "quantity": "1.000"}]},
    )
    assert response.json()["receive_status"] == "partial_received"


def test_full_receiving_sets_received_status(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token, "2.000")
    set_initial_stock(client, token, product["id"], "10.000")
    confirmed = confirm_order(client, token, order["id"])
    response = client.post(
        f"/api/purchase-orders/{order['id']}/receive",
        headers=auth_headers(token),
        json={"items": [{"item_id": confirmed["items"][0]["id"], "quantity": "2.000"}]},
    )
    assert response.json()["receive_status"] == "received"


def test_payment_creates_purchase_payment(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    response = client.post(
        f"/api/purchase-orders/{order['id']}/payments",
        headers=auth_headers(token),
        json={"payment_date": "2026-04-30", "amount": "5.00", "method": "cash"},
    )
    assert response.status_code == 200
    assert len(response.json()["payments"]) == 1


def test_payment_updates_paid_unpaid_and_status(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    response = client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "5.00", "method": "cash"})
    data = response.json()
    assert data["paid_amount"] == "5.00"
    assert data["unpaid_amount"] == "15.00"
    assert data["payment_status"] == "partial_paid"


def test_payment_reduces_supplier_payable(client: TestClient) -> None:
    token = login(client)
    supplier, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "5.00", "method": "cash"})
    assert get_supplier(client, token, supplier["id"])["current_payable"] == "15.00"


def test_payment_amount_cannot_exceed_unpaid_amount(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    response = client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "25.00", "method": "cash"})
    assert response.status_code == 400


def test_draft_order_cannot_be_paid(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    response = client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "1.00", "method": "cash"})
    assert response.status_code == 400


def test_can_cancel_draft_order(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    response = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "供应商取消"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_confirmed_unpaid_order_reduces_supplier_payable(client: TestClient) -> None:
    token = login(client)
    supplier, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    response = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "供应商取消"})
    assert response.status_code == 200
    assert get_supplier(client, token, supplier["id"])["current_payable"] == "0.00"


def test_cancel_received_order_creates_cancel_reverse_movement(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    set_initial_stock(client, token, product["id"], "10.000")
    confirmed = confirm_order(client, token, order["id"])
    client.post(f"/api/purchase-orders/{order['id']}/receive", headers=auth_headers(token), json={"items": [{"item_id": confirmed["items"][0]["id"], "quantity": "2.000"}]})
    response = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "供应商取消"})
    assert response.status_code == 200
    movements = client.get("/api/stock-movements?movement_type=cancel_reverse", headers=auth_headers(token)).json()
    assert movements["total"] == 1
    assert get_inventory(client, token, product["id"])["quantity_on_hand"] == "10.000"


def test_cancel_received_order_fails_when_reverse_would_make_inventory_negative(client: TestClient) -> None:
    token = login(client)
    _, product, order = create_basic_order(client, token)
    confirmed = confirm_order(client, token, order["id"])
    client.post(f"/api/purchase-orders/{order['id']}/receive", headers=auth_headers(token), json={"items": [{"item_id": confirmed["items"][0]["id"], "quantity": "2.000"}]})
    response = client.post(
        "/api/inventory/adjustments",
        headers=auth_headers(token),
        json={"product_id": product["id"], "mode": "decrease", "quantity": "1.500", "remark": "制造反冲不足场景"},
    )
    assert response.status_code == 200
    response = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "供应商取消"})
    assert response.status_code == 400


def test_paid_order_cannot_be_cancelled_in_first_version(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "1.00", "method": "cash"})
    response = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "供应商取消"})
    assert response.status_code == 400


def test_cancelled_order_cannot_be_edited_confirmed_received_or_paid(client: TestClient) -> None:
    token = login(client)
    supplier, product, order = create_basic_order(client, token)
    client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "供应商取消"})
    edit_response = client.put(
        f"/api/purchase-orders/{order['id']}",
        headers=auth_headers(token),
        json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "1.00"}]},
    )
    confirm_response = client.post(f"/api/purchase-orders/{order['id']}/confirm", headers=auth_headers(token))
    receive_response = client.post(f"/api/purchase-orders/{order['id']}/receive", headers=auth_headers(token), json={"items": [{"item_id": order["items"][0]["id"], "quantity": "1.000"}]})
    pay_response = client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "1.00", "method": "cash"})
    assert edit_response.status_code == 400
    assert confirm_response.status_code == 400
    assert receive_response.status_code == 400
    assert pay_response.status_code == 400


def test_purchase_order_list_supports_pagination(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    for index in range(3):
        product = create_product(client, token, f"分页采购产品{index}")
        create_order(client, token, supplier["id"], product["id"])
    response = client.get("/api/purchase-orders?page=1&page_size=2", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2


def test_purchase_order_list_supports_keyword_search(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token, "杭州采购供应商")
    product = create_product(client, token, "关键词采购产品")
    create_order(client, token, supplier["id"], product["id"])
    response = client.get("/api/purchase-orders?keyword=杭州", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_purchase_order_detail_returns_items_and_payments(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    confirm_order(client, token, order["id"])
    client.post(f"/api/purchase-orders/{order['id']}/payments", headers=auth_headers(token), json={"amount": "5.00", "method": "cash"})
    response = client.get(f"/api/purchase-orders/{order['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert len(response.json()["payments"]) == 1


def test_money_fields_use_numeric_and_serialize_safely(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token)
    columns = inspect(PurchaseOrder).columns
    assert isinstance(columns.payable_amount.type, Numeric)
    assert order["payable_amount"] == "20.00"
    assert Decimal(order["payable_amount"]) == Decimal("20.00")


def test_quantity_fields_use_numeric_and_serialize_safely(client: TestClient) -> None:
    token = login(client)
    _, _, order = create_basic_order(client, token, "1.235")
    columns = inspect(PurchaseOrderItem).columns
    assert isinstance(columns.quantity.type, Numeric)
    assert order["total_quantity"] == "1.235"
    assert order["items"][0]["quantity"] == "1.235"
