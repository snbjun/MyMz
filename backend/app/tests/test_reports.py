from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.deps import get_db
from app.main import create_app
from app.modules.auth.service import init_admin_user
from app.modules.customers.model import CustomerCategory
from app.modules.finance.model import FinanceAccount, FinanceCategory
from app.modules.inventory.model import Warehouse
from app.modules.products.model import ProductCategory, ProductUnit
from app.modules.suppliers.model import SupplierCategory


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 10 阶段新增：报表测试使用临时库，并通过业务 API 造数验证统计口径。"""

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
        db.add(FinanceCategory(name="其他收入", type="income", sort_order=0, is_default=True, is_active=True))
        db.add(FinanceCategory(name="其他支出", type="expense", sort_order=0, is_default=True, is_active=True))
        db.add(
            FinanceAccount(
                name="现金",
                type="cash",
                opening_balance=Decimal("0.00"),
                current_balance=Decimal("0.00"),
                sort_order=0,
                is_default=True,
                is_active=True,
            )
        )
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


def create_customer(client: TestClient, token: str, name: str = "报表客户") -> dict:
    response = client.post(
        "/api/customers",
        headers=auth_headers(token),
        json={"name": name, "opening_receivable": "0.00", "current_receivable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_supplier(client: TestClient, token: str, name: str = "报表供应商") -> dict:
    response = client.post(
        "/api/suppliers",
        headers=auth_headers(token),
        json={"name": name, "opening_payable": "0.00", "current_payable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_product(client: TestClient, token: str, name: str = "报表产品", warning_qty: str = "10.000") -> dict:
    response = client.post(
        "/api/products",
        headers=auth_headers(token),
        json={
            "code": f"R-{name}",
            "barcode": f"RB-{name}",
            "name": name,
            "sale_price": "20.00",
            "purchase_price": "5.00",
            "wholesale_price": "10.00",
            "stock_warning_qty": warning_qty,
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_sales_order(client: TestClient, token: str, customer_id: int, product_id: int, date: str = "2026-05-01") -> dict:
    response = client.post(
        "/api/sales-orders",
        headers=auth_headers(token),
        json={
            "customer_id": customer_id,
            "order_date": date,
            "discount_amount": "0.00",
            "items": [{"product_id": product_id, "quantity": "2.000", "unit_price": "20.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_purchase_order(client: TestClient, token: str, supplier_id: int, product_id: int, date: str = "2026-05-01") -> dict:
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={
            "supplier_id": supplier_id,
            "order_date": date,
            "discount_amount": "0.00",
            "items": [{"product_id": product_id, "quantity": "3.000", "unit_price": "5.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def confirm_sales(client: TestClient, token: str, order_id: int) -> dict:
    response = client.post(f"/api/sales-orders/{order_id}/confirm", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json())


def confirm_purchase(client: TestClient, token: str, order_id: int) -> dict:
    response = client.post(f"/api/purchase-orders/{order_id}/confirm", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json())


def create_basic_report_data(client: TestClient, token: str) -> dict:
    customer = create_customer(client, token)
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    sales = confirm_sales(client, token, create_sales_order(client, token, customer["id"], product["id"])["id"])
    payment_response = client.post(
        f"/api/sales-orders/{sales['id']}/payments",
        headers=auth_headers(token),
        json={"payment_date": "2026-05-01", "amount": "10.00", "method": "cash"},
    )
    assert payment_response.status_code == 200
    purchase = confirm_purchase(client, token, create_purchase_order(client, token, supplier["id"], product["id"])["id"])
    pay_response = client.post(
        f"/api/purchase-orders/{purchase['id']}/payments",
        headers=auth_headers(token),
        json={"payment_date": "2026-05-01", "amount": "5.00", "method": "cash"},
    )
    assert pay_response.status_code == 200
    stock_response = client.post(
        "/api/inventory/initial-stock",
        headers=auth_headers(token),
        json={"product_id": product["id"], "quantity": "5.000", "unit_cost": "2.0000"},
    )
    assert stock_response.status_code == 200
    categories = client.get("/api/finance-categories", headers=auth_headers(token)).json()
    income_category = next(item for item in categories if item["type"] == "income")
    expense_category = next(item for item in categories if item["type"] == "expense")
    account = client.get("/api/finance-accounts", headers=auth_headers(token)).json()[0]
    income = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "income", "record_date": "2026-05-01", "category_id": income_category["id"], "account_id": account["id"], "amount": "7.00"},
    )
    expense = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "expense", "record_date": "2026-05-01", "category_id": expense_category["id"], "account_id": account["id"], "amount": "2.00"},
    )
    voided = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "income", "record_date": "2026-05-01", "category_id": income_category["id"], "account_id": account["id"], "amount": "99.00"},
    )
    assert income.status_code == 200
    assert expense.status_code == 200
    assert voided.status_code == 200
    void_response = client.post(f"/api/finance-records/{voided.json()['id']}/void", headers=auth_headers(token), json={"reason": "测试作废"})
    assert void_response.status_code == 200
    return {"customer": customer, "supplier": supplier, "product": product}


def report_params() -> str:
    return "start_date=2026-05-01&end_date=2026-05-31"


def test_anonymous_user_cannot_access_report_overview(client: TestClient) -> None:
    response = client.get("/api/reports/overview")
    assert response.status_code == 401


def test_default_date_range_is_available(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/reports/overview", headers=auth_headers(token))
    assert response.status_code == 200
    assert "start_date" in response.json()
    assert "end_date" in response.json()


def test_draft_sales_order_is_not_counted(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token)
    product = create_product(client, token)
    create_sales_order(client, token, customer["id"], product["id"])
    response = client.get(f"/api/reports/sales/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["order_count"] == 0


def test_cancelled_sales_order_is_not_counted(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token)
    product = create_product(client, token)
    order = confirm_sales(client, token, create_sales_order(client, token, customer["id"], product["id"])["id"])
    cancel = client.post(f"/api/sales-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "测试作废"})
    assert cancel.status_code == 200
    response = client.get(f"/api/reports/sales/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["order_count"] == 0


def test_confirmed_sales_order_is_counted(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token)
    product = create_product(client, token)
    confirm_sales(client, token, create_sales_order(client, token, customer["id"], product["id"])["id"])
    response = client.get(f"/api/reports/sales/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["order_count"] == 1
    assert response.json()["receivable_amount"] == "40.00"


def test_sales_by_customer_is_correct(client: TestClient) -> None:
    token = login(client)
    data = create_basic_report_data(client, token)
    response = client.get(f"/api/reports/sales/by-customer?{report_params()}", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["customer_id"] == data["customer"]["id"]
    assert item["sales_amount"] == "40.00"


def test_sales_by_product_is_correct(client: TestClient) -> None:
    token = login(client)
    data = create_basic_report_data(client, token)
    response = client.get(f"/api/reports/sales/by-product?{report_params()}", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["product_id"] == data["product"]["id"]
    assert item["quantity"] == "2.000"
    assert item["sales_amount"] == "40.00"


def test_draft_purchase_order_is_not_counted(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    create_purchase_order(client, token, supplier["id"], product["id"])
    response = client.get(f"/api/reports/purchase/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["order_count"] == 0


def test_cancelled_purchase_order_is_not_counted(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    order = confirm_purchase(client, token, create_purchase_order(client, token, supplier["id"], product["id"])["id"])
    cancel = client.post(f"/api/purchase-orders/{order['id']}/cancel", headers=auth_headers(token), json={"reason": "测试作废"})
    assert cancel.status_code == 200
    response = client.get(f"/api/reports/purchase/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["order_count"] == 0


def test_confirmed_purchase_order_is_counted(client: TestClient) -> None:
    token = login(client)
    supplier = create_supplier(client, token)
    product = create_product(client, token)
    confirm_purchase(client, token, create_purchase_order(client, token, supplier["id"], product["id"])["id"])
    response = client.get(f"/api/reports/purchase/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["order_count"] == 1
    assert response.json()["payable_amount"] == "15.00"


def test_purchase_by_supplier_is_correct(client: TestClient) -> None:
    token = login(client)
    data = create_basic_report_data(client, token)
    response = client.get(f"/api/reports/purchase/by-supplier?{report_params()}", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["supplier_id"] == data["supplier"]["id"]
    assert item["purchase_amount"] == "15.00"


def test_purchase_by_product_is_correct(client: TestClient) -> None:
    token = login(client)
    data = create_basic_report_data(client, token)
    response = client.get(f"/api/reports/purchase/by-product?{report_params()}", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["product_id"] == data["product"]["id"]
    assert item["quantity"] == "3.000"
    assert item["purchase_amount"] == "15.00"


def test_receivable_report_reads_customer_current_receivable(client: TestClient) -> None:
    token = login(client)
    data = create_basic_report_data(client, token)
    response = client.get("/api/reports/receivables", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["customer_id"] == data["customer"]["id"]
    assert item["current_receivable"] == "30.00"


def test_payable_report_reads_supplier_current_payable(client: TestClient) -> None:
    token = login(client)
    data = create_basic_report_data(client, token)
    response = client.get("/api/reports/payables", headers=auth_headers(token))
    item = response.json()["items"][0]
    assert item["supplier_id"] == data["supplier"]["id"]
    assert item["current_payable"] == "10.00"


def test_inventory_summary_reads_current_inventory(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get("/api/reports/inventory/summary", headers=auth_headers(token))
    assert response.json()["total_quantity"] == "5.000"
    assert response.json()["total_cost"] == "10.00"


def test_low_stock_count_is_correct(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get("/api/reports/inventory/summary", headers=auth_headers(token))
    assert response.json()["low_stock_count"] == 1


def test_inventory_movement_summary_groups_by_type(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(
        "/api/reports/inventory/movement-summary?start_date=2000-01-01&end_date=2099-12-31",
        headers=auth_headers(token),
    )
    assert response.json()["in_quantity"] == "5.000"
    assert response.json()["items"][0]["movement_type"] == "initial"


def test_finance_summary_reads_account_balance(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/finance/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["balance_total"] == "5.00"


def test_voided_finance_records_are_not_counted(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/finance/summary?{report_params()}", headers=auth_headers(token))
    assert response.json()["income_amount"] == "7.00"


def test_finance_income_expense_and_net_are_correct(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/finance/summary?{report_params()}", headers=auth_headers(token))
    data = response.json()
    assert data["income_amount"] == "7.00"
    assert data["expense_amount"] == "2.00"
    assert data["net_amount"] == "5.00"


def test_profit_overview_uses_defined_formula(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/profit?{report_params()}", headers=auth_headers(token))
    data = response.json()
    assert data["gross_profit"] == "25.00"
    assert data["finance_net_amount"] == "5.00"
    assert data["estimated_net_profit"] == "30.00"


def test_paged_report_returns_total_page_and_page_size(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/sales/by-customer?{report_params()}&page=1&page_size=1", headers=auth_headers(token))
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 1


def test_money_fields_serialize_safely(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/overview?{report_params()}", headers=auth_headers(token))
    assert response.json()["sales_summary"]["receivable_amount"] == "40.00"


def test_quantity_fields_serialize_safely(client: TestClient) -> None:
    token = login(client)
    create_basic_report_data(client, token)
    response = client.get(f"/api/reports/overview?{report_params()}", headers=auth_headers(token))
    assert response.json()["sales_summary"]["total_quantity"] == "2.000"
