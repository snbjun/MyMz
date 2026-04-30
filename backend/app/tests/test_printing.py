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
from app.modules.customers.model import CustomerCategory
from app.modules.inventory.model import Warehouse
from app.modules.print_templates.model import PrintSetting
from app.modules.products.model import ProductCategory, ProductUnit
from app.modules.purchase.model import PurchaseOrder, PurchaseOrderItem
from app.modules.sales.model import SalesOrder, SalesOrderItem
from app.modules.suppliers.model import SupplierCategory


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 11 阶段新增：打印测试使用临时 SQLite，避免污染 data/app.db。"""

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


def create_customer(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/customers",
        headers=auth_headers(token),
        json={
            "name": "打印客户",
            "phone": "13800000000",
            "address": "客户地址",
            "opening_receivable": "0.00",
            "current_receivable": "0.00",
            "credit_limit": "0.00",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_supplier(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/suppliers",
        headers=auth_headers(token),
        json={
            "name": "打印供应商",
            "phone": "13900000000",
            "address": "供应商地址",
            "opening_payable": "0.00",
            "current_payable": "0.00",
            "credit_limit": "0.00",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_product(client: TestClient, token: str, name: str = "打印产品") -> dict:
    response = client.post(
        "/api/products",
        headers=auth_headers(token),
        json={
            "code": f"PR-{name}",
            "barcode": f"BAR-{name}",
            "name": name,
            "spec": "标准",
            "model": "M1",
            "sale_price": "10.00",
            "purchase_price": "8.00",
            "wholesale_price": "9.00",
            "stock_warning_qty": "0.000",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_sales_order(client: TestClient, token: str) -> dict:
    customer = create_customer(client, token)
    product = create_product(client, token, "销售打印产品")
    response = client.post(
        "/api/sales-orders",
        headers=auth_headers(token),
        json={
            "customer_id": customer["id"],
            "order_date": "2026-05-01",
            "discount_amount": "1.00",
            "remark": "销售打印备注",
            "items": [{"product_id": product["id"], "quantity": "2.000", "unit_price": "10.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_purchase_order(client: TestClient, token: str) -> dict:
    supplier = create_supplier(client, token)
    product = create_product(client, token, "采购打印产品")
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={
            "supplier_id": supplier["id"],
            "order_date": "2026-05-01",
            "discount_amount": "1.00",
            "remark": "采购打印备注",
            "items": [{"product_id": product["id"], "quantity": "3.000", "unit_price": "8.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def test_anonymous_user_cannot_access_print_settings(client: TestClient) -> None:
    response = client.get("/api/print-settings")
    assert response.status_code == 401


def test_can_get_default_sales_print_setting(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/print-settings/sales_order", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["doc_type"] == "sales_order"
    assert response.json()["template_name"] == "标准模板"


def test_can_get_default_purchase_print_setting(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/print-settings/purchase_order", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["doc_type"] == "purchase_order"
    assert response.json()["paper_size"] == "A4"


def test_can_update_sales_print_setting(client: TestClient) -> None:
    token = login(client)
    response = client.put(
        "/api/print-settings/sales_order",
        headers=auth_headers(token),
        json={"template_name": "销售标准", "show_company_name": True, "company_name": "测试公司", "show_unit_price": False},
    )
    assert response.status_code == 200
    assert response.json()["template_name"] == "销售标准"
    assert response.json()["company_name"] == "测试公司"
    assert response.json()["show_unit_price"] is False


def test_invalid_doc_type_returns_error(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/print-settings/other", headers=auth_headers(token))
    assert response.status_code == 400


def test_can_get_sales_order_print_data(client: TestClient) -> None:
    token = login(client)
    order = create_sales_order(client, token)
    response = client.get(f"/api/print/sales-orders/{order['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["order_no"] == order["order_no"]
    assert data["customer_name"] == "打印客户"
    assert data["customer_phone"] == "13800000000"
    assert data["warehouse_name"] == "默认仓库"
    assert data["payment_summary"]["amount"] == "0.00"


def test_can_get_purchase_order_print_data(client: TestClient) -> None:
    token = login(client)
    order = create_purchase_order(client, token)
    response = client.get(f"/api/print/purchase-orders/{order['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["order_no"] == order["order_no"]
    assert data["supplier_name"] == "打印供应商"
    assert data["supplier_phone"] == "13900000000"
    assert data["warehouse_name"] == "默认仓库"


def test_print_data_does_not_modify_sales_or_purchase_status(client: TestClient) -> None:
    token = login(client)
    sales_order = create_sales_order(client, token)
    purchase_order = create_purchase_order(client, token)
    client.get(f"/api/print/sales-orders/{sales_order['id']}", headers=auth_headers(token))
    client.get(f"/api/print/purchase-orders/{purchase_order['id']}", headers=auth_headers(token))
    sales_detail = client.get(f"/api/sales-orders/{sales_order['id']}", headers=auth_headers(token)).json()
    purchase_detail = client.get(f"/api/purchase-orders/{purchase_order['id']}", headers=auth_headers(token)).json()
    assert sales_detail["status"] == "draft"
    assert purchase_detail["status"] == "draft"


def test_cancelled_sales_order_can_return_print_data(client: TestClient) -> None:
    token = login(client)
    order = create_sales_order(client, token)
    cancel_response = client.post(f"/api/sales-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "测试作废"})
    assert cancel_response.status_code == 200
    response = client.get(f"/api/print/sales-orders/{order['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancelled_purchase_order_can_return_print_data(client: TestClient) -> None:
    token = login(client)
    order = create_purchase_order(client, token)
    cancel_response = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "测试作废"})
    assert cancel_response.status_code == 200
    response = client.get(f"/api/print/purchase-orders/{order['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_print_money_fields_serialize_safely(client: TestClient) -> None:
    token = login(client)
    order = create_sales_order(client, token)
    columns = inspect(PrintSetting).columns
    sales_columns = inspect(SalesOrder).columns
    purchase_columns = inspect(PurchaseOrder).columns
    assert columns.doc_type.type.length == 32
    assert isinstance(sales_columns.receivable_amount.type, Numeric)
    assert isinstance(purchase_columns.payable_amount.type, Numeric)
    data = client.get(f"/api/print/sales-orders/{order['id']}", headers=auth_headers(token)).json()
    assert data["receivable_amount"] == "19.00"
    assert Decimal(data["items"][0]["line_amount"]) == Decimal("20.00")


def test_print_quantity_fields_serialize_safely(client: TestClient) -> None:
    token = login(client)
    order = create_purchase_order(client, token)
    sales_columns = inspect(SalesOrderItem).columns
    purchase_columns = inspect(PurchaseOrderItem).columns
    assert isinstance(sales_columns.quantity.type, Numeric)
    assert isinstance(purchase_columns.quantity.type, Numeric)
    data = client.get(f"/api/print/purchase-orders/{order['id']}", headers=auth_headers(token)).json()
    assert data["total_quantity"] == "3.000"
    assert data["items"][0]["quantity"] == "3.000"
