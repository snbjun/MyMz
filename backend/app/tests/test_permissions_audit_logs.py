from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.deps import get_db
from app.core.permissions import Permission, has_permission
from app.main import create_app
from app.modules.auth.service import init_admin_user
from app.modules.customers.model import CustomerCategory
from app.modules.finance.model import FinanceAccount, FinanceCategory
from app.modules.inventory.model import Warehouse
from app.modules.products.model import ProductCategory, ProductUnit
from app.modules.suppliers.model import SupplierCategory


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    """Phase 13: use a temporary database and data directory for permission/audit tests."""

    data_dir = tmp_path / "data"
    uploads_dir = data_dir / "uploads"
    backups_dir = data_dir / "backups"
    uploads_dir.mkdir(parents=True)
    backups_dir.mkdir(parents=True)
    database_path = data_dir / "app.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setattr(settings, "data_dir", str(data_dir))
    monkeypatch.setattr(settings, "uploads_dir", str(uploads_dir))
    monkeypatch.setattr(settings, "backups_dir", str(backups_dir))
    monkeypatch.setattr(settings, "database_url", database_url)

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
        admin = init_admin_user(db, username="admin", password="admin123456", display_name="Admin")
        db.add_all(
            [
                CustomerCategory(name="Default", sort_order=0, is_default=True),
                SupplierCategory(name="Default", sort_order=0, is_default=True),
                ProductCategory(name="Default", sort_order=0, is_default=True),
                ProductUnit(name="pcs", sort_order=0, is_default=True),
                Warehouse(name="Default", sort_order=0, is_default=True, is_active=True),
                FinanceCategory(name="Other income", type="income", sort_order=0, is_default=True, is_active=True),
                FinanceCategory(name="Other expense", type="expense", sort_order=0, is_default=True, is_active=True),
                FinanceAccount(
                    name="Cash",
                    type="cash",
                    opening_balance="0.00",
                    current_balance="0.00",
                    sort_order=0,
                    is_default=True,
                    is_active=True,
                ),
            ]
        )
        db.commit()
        assert admin.is_superuser

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, username: str = "admin", password: str = "admin123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def create_role_user(client: TestClient, admin_token: str, username: str, role: str) -> str:
    response = client.post(
        "/api/users",
        headers=auth_headers(admin_token),
        json={
            "username": username,
            "display_name": username,
            "password": "user123456",
            "role": role,
            "is_active": True,
            "is_superuser": False,
        },
    )
    assert response.status_code == 200
    return login(client, username, "user123456")


def create_customer(client: TestClient, token: str, name: str = "CustomerA") -> dict:
    response = client.post(
        "/api/customers",
        headers=auth_headers(token),
        json={"name": name, "opening_receivable": "0.00", "current_receivable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_supplier(client: TestClient, token: str, name: str = "SupplierA") -> dict:
    response = client.post(
        "/api/suppliers",
        headers=auth_headers(token),
        json={"name": name, "opening_payable": "0.00", "current_payable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_product(client: TestClient, token: str, name: str = "ProductA") -> dict:
    response = client.post(
        "/api/products",
        headers=auth_headers(token),
        json={
            "code": f"CODE-{name}",
            "barcode": f"BAR-{name}",
            "name": name,
            "sale_price": "10.00",
            "purchase_price": "5.00",
            "wholesale_price": "8.00",
            "stock_warning_qty": "0.000",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_sales_order(client: TestClient, token: str, customer_id: int, product_id: int) -> dict:
    response = client.post(
        "/api/sales-orders",
        headers=auth_headers(token),
        json={
            "customer_id": customer_id,
            "order_date": "2026-05-01",
            "discount_amount": "0.00",
            "items": [{"product_id": product_id, "quantity": "1.000", "unit_price": "10.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def create_purchase_order(client: TestClient, token: str, supplier_id: int, product_id: int) -> dict:
    response = client.post(
        "/api/purchase-orders",
        headers=auth_headers(token),
        json={
            "supplier_id": supplier_id,
            "order_date": "2026-05-01",
            "discount_amount": "0.00",
            "items": [{"product_id": product_id, "quantity": "1.000", "unit_price": "5.00", "discount_amount": "0.00"}],
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def get_default_finance_refs(client: TestClient, token: str) -> tuple[int, int]:
    categories = client.get("/api/finance-categories?type=income", headers=auth_headers(token))
    accounts = client.get("/api/finance-accounts", headers=auth_headers(token))
    assert categories.status_code == 200
    assert accounts.status_code == 200
    return categories.json()[0]["id"], accounts.json()[0]["id"]


def list_audit_logs(client: TestClient, token: str, **params) -> dict:
    response = client.get("/api/audit-logs", headers=auth_headers(token), params=params)
    assert response.status_code == 200
    return dict(response.json())


def test_superuser_has_all_permissions(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    user = type("UserLike", (), response.json())()
    for permission in Permission:
        assert has_permission(user, permission)


def test_staff_can_write_business_but_cannot_manage_users_or_backups(client: TestClient) -> None:
    admin_token = login(client)
    staff_token = create_role_user(client, admin_token, "staff1", "staff")
    response = client.post(
        "/api/customers",
        headers=auth_headers(staff_token),
        json={"name": "StaffCustomer", "opening_receivable": "0.00", "current_receivable": "0.00", "credit_limit": "0.00"},
    )
    assert response.status_code == 200
    assert client.get("/api/users", headers=auth_headers(staff_token)).status_code == 403
    assert client.get("/api/backups", headers=auth_headers(staff_token)).status_code == 403


def test_viewer_can_read_reports_and_sales_but_cannot_write_business(client: TestClient) -> None:
    admin_token = login(client)
    viewer_token = create_role_user(client, admin_token, "viewer1", "viewer")
    customer = create_customer(client, admin_token, "ReadonlyCustomer")
    product = create_product(client, admin_token, "ReadonlyProduct")
    category_id, account_id = get_default_finance_refs(client, admin_token)

    assert client.get("/api/reports/overview", headers=auth_headers(viewer_token)).status_code == 200
    assert client.get("/api/sales-orders", headers=auth_headers(viewer_token)).status_code == 200
    response = client.post(
        "/api/sales-orders",
        headers=auth_headers(viewer_token),
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": product["id"], "quantity": "1.000", "unit_price": "10.00"}],
        },
    )
    assert response.status_code == 403
    response = client.post(
        "/api/inventory/adjustments",
        headers=auth_headers(viewer_token),
        json={"product_id": product["id"], "mode": "increase", "quantity": "1.000", "unit_cost": "5.0000"},
    )
    assert response.status_code == 403
    response = client.post(
        "/api/finance-records",
        headers=auth_headers(viewer_token),
        json={
            "type": "income",
            "record_date": "2026-05-01",
            "category_id": category_id,
            "account_id": account_id,
            "amount": "1.00",
        },
    )
    assert response.status_code == 403
    response = client.put(
        "/api/print-settings/sales_order",
        headers=auth_headers(viewer_token),
        json={"template_name": "Viewer cannot update"},
    )
    assert response.status_code == 403


def test_audit_log_access_requires_admin_or_superuser(client: TestClient) -> None:
    admin_token = login(client)
    staff_token = create_role_user(client, admin_token, "staff2", "staff")
    audit_admin_token = create_role_user(client, admin_token, "admin2", "admin")
    assert client.get("/api/audit-logs").status_code == 401
    assert client.get("/api/audit-logs", headers=auth_headers(staff_token)).status_code == 403
    assert client.get("/api/audit-logs", headers=auth_headers(audit_admin_token)).status_code == 200
    assert client.get("/api/audit-logs", headers=auth_headers(admin_token)).status_code == 200


def test_key_business_actions_write_audit_logs_without_secrets(client: TestClient) -> None:
    token = login(client)
    customer = create_customer(client, token, "AuditCustomer")
    supplier = create_supplier(client, token, "AuditSupplier")
    product = create_product(client, token, "AuditProduct")
    sales_order = create_sales_order(client, token, customer["id"], product["id"])
    purchase_order = create_purchase_order(client, token, supplier["id"], product["id"])
    category_id, account_id = get_default_finance_refs(client, token)

    client.post(
        "/api/inventory/adjustments",
        headers=auth_headers(token),
        json={"product_id": product["id"], "mode": "increase", "quantity": "2.000", "unit_cost": "5.0000"},
    )
    client.post(f"/api/sales-orders/{sales_order['id']}/confirm", headers=auth_headers(token))
    client.post(f"/api/purchase-orders/{purchase_order['id']}/confirm", headers=auth_headers(token))
    client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={
            "type": "income",
            "record_date": "2026-05-01",
            "category_id": category_id,
            "account_id": account_id,
            "amount": "3.00",
            "summary": "AuditIncome",
        },
    )
    client.post("/api/backups", headers=auth_headers(token), json={"note": "AuditBackup"})

    logs = list_audit_logs(client, token, page=1, page_size=50)
    actions = {(item["module"], item["action"]) for item in logs["items"]}
    assert ("auth", "login") in actions
    assert ("customers", "create") in actions
    assert ("inventory", "adjust") in actions
    assert ("sales", "confirm") in actions
    assert ("purchase", "confirm") in actions
    assert ("finance", "create_record") in actions
    assert ("backups", "create") in actions
    searchable_text = "\n".join(
        f"{item.get('summary') or ''} {item.get('path') or ''} {item.get('target_label') or ''}"
        for item in logs["items"]
    )
    assert "admin123456" not in searchable_text
    assert "Bearer" not in searchable_text
    assert "token" not in searchable_text.lower()


def test_audit_log_list_search_pagination_and_detail(client: TestClient) -> None:
    token = login(client)
    create_customer(client, token, "SearchLogCustomer")
    create_customer(client, token, "PagedLogCustomer")
    page = list_audit_logs(client, token, page=1, page_size=1)
    assert page["total"] >= 2
    assert page["page"] == 1
    assert page["page_size"] == 1
    assert len(page["items"]) == 1
    searched = list_audit_logs(client, token, keyword="SearchLogCustomer")
    assert searched["total"] >= 1
    log_id = searched["items"][0]["id"]
    detail = client.get(f"/api/audit-logs/{log_id}", headers=auth_headers(token))
    assert detail.status_code == 200
    assert detail.json()["id"] == log_id
