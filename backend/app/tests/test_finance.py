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
from app.modules.finance.model import FinanceAccount, FinanceCategory, FinanceRecord


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    """第 9 阶段新增：费用收入测试使用临时 SQLite，避免污染本地正式数据库。"""

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


def default_income_category(client: TestClient, token: str) -> dict:
    response = client.get("/api/finance-categories?type=income", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json()[0])


def default_expense_category(client: TestClient, token: str) -> dict:
    response = client.get("/api/finance-categories?type=expense", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json()[0])


def default_account(client: TestClient, token: str) -> dict:
    response = client.get("/api/finance-accounts", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json()[0])


def create_category(client: TestClient, token: str, name: str, category_type: str) -> dict:
    response = client.post(
        "/api/finance-categories",
        headers=auth_headers(token),
        json={"name": name, "type": category_type, "sort_order": 1, "is_default": False, "is_active": True},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_account(client: TestClient, token: str, name: str = "银行账户", opening_balance: str = "100.00") -> dict:
    response = client.post(
        "/api/finance-accounts",
        headers=auth_headers(token),
        json={"name": name, "type": "bank", "opening_balance": opening_balance, "sort_order": 1, "is_active": True},
    )
    assert response.status_code == 200
    return dict(response.json())


def create_record(
    client: TestClient,
    token: str,
    record_type: str,
    category_id: int,
    account_id: int,
    amount: str = "20.00",
    summary: str = "测试流水",
) -> dict:
    response = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={
            "type": record_type,
            "record_date": "2026-04-30",
            "category_id": category_id,
            "account_id": account_id,
            "amount": amount,
            "summary": summary,
            "remark": "费用收入测试",
        },
    )
    assert response.status_code == 200
    return dict(response.json())


def get_account(client: TestClient, token: str, account_id: int) -> dict:
    response = client.get(f"/api/finance-accounts/{account_id}", headers=auth_headers(token))
    assert response.status_code == 200
    return dict(response.json())


def test_anonymous_user_cannot_access_finance_record_list(client: TestClient) -> None:
    response = client.get("/api/finance-records")
    assert response.status_code == 401


def test_default_categories_and_account_can_be_queried(client: TestClient) -> None:
    token = login(client)
    categories = client.get("/api/finance-categories", headers=auth_headers(token)).json()
    accounts = client.get("/api/finance-accounts", headers=auth_headers(token)).json()
    assert {item["type"] for item in categories} == {"income", "expense"}
    assert accounts[0]["name"] == "现金"


def test_can_create_income_category(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "服务收入", "income")
    assert category["name"] == "服务收入"


def test_same_type_category_name_cannot_duplicate(client: TestClient) -> None:
    token = login(client)
    create_category(client, token, "重复分类", "income")
    response = client.post("/api/finance-categories", headers=auth_headers(token), json={"name": "重复分类", "type": "income"})
    assert response.status_code == 400


def test_same_category_name_can_exist_in_different_types(client: TestClient) -> None:
    token = login(client)
    create_category(client, token, "通用分类", "income")
    category = create_category(client, token, "通用分类", "expense")
    assert category["type"] == "expense"


def test_category_used_by_normal_record_cannot_be_deleted(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "不可删除收入", "income")
    account = default_account(client, token)
    create_record(client, token, "income", category["id"], account["id"])
    response = client.delete(f"/api/finance-categories/{category['id']}", headers=auth_headers(token))
    assert response.status_code == 400


def test_disabled_category_cannot_be_used_for_new_record(client: TestClient) -> None:
    token = login(client)
    category = create_category(client, token, "禁用收入", "income")
    account = default_account(client, token)
    toggle = client.post(f"/api/finance-categories/{category['id']}/toggle-active", headers=auth_headers(token))
    assert toggle.status_code == 200
    response = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "income", "category_id": category["id"], "account_id": account["id"], "amount": "1.00"},
    )
    assert response.status_code == 400


def test_can_create_finance_account(client: TestClient) -> None:
    token = login(client)
    account = create_account(client, token)
    assert account["name"] == "银行账户"


def test_account_name_cannot_duplicate_when_not_deleted(client: TestClient) -> None:
    token = login(client)
    create_account(client, token, "重复账户")
    response = client.post("/api/finance-accounts", headers=auth_headers(token), json={"name": "重复账户", "type": "bank"})
    assert response.status_code == 400


def test_current_balance_equals_opening_balance_when_creating_account(client: TestClient) -> None:
    token = login(client)
    account = create_account(client, token, "期初账户", "88.88")
    assert account["current_balance"] == "88.88"


def test_account_with_records_cannot_update_opening_balance(client: TestClient) -> None:
    token = login(client)
    account = create_account(client, token, "锁定期初账户")
    category = default_income_category(client, token)
    create_record(client, token, "income", category["id"], account["id"])
    response = client.put(
        f"/api/finance-accounts/{account['id']}",
        headers=auth_headers(token),
        json={"opening_balance": "99.00"},
    )
    assert response.status_code == 400


def test_account_with_records_cannot_be_deleted(client: TestClient) -> None:
    token = login(client)
    account = create_account(client, token, "不可删除账户")
    category = default_income_category(client, token)
    create_record(client, token, "income", category["id"], account["id"])
    response = client.delete(f"/api/finance-accounts/{account['id']}", headers=auth_headers(token))
    assert response.status_code == 400


def test_disabled_account_cannot_be_used_for_new_record(client: TestClient) -> None:
    token = login(client)
    account = create_account(client, token, "禁用账户")
    category = default_income_category(client, token)
    toggle = client.post(f"/api/finance-accounts/{account['id']}/toggle-active", headers=auth_headers(token))
    assert toggle.status_code == 200
    response = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "income", "category_id": category["id"], "account_id": account["id"], "amount": "1.00"},
    )
    assert response.status_code == 400


def test_income_record_increases_account_balance(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    create_record(client, token, "income", category["id"], account["id"], "30.00")
    assert get_account(client, token, account["id"])["current_balance"] == "30.00"


def test_expense_record_decreases_account_balance(client: TestClient) -> None:
    token = login(client)
    category = default_expense_category(client, token)
    account = default_account(client, token)
    create_record(client, token, "expense", category["id"], account["id"], "15.00")
    assert get_account(client, token, account["id"])["current_balance"] == "-15.00"


def test_record_category_type_must_match_record_type(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    response = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "expense", "category_id": category["id"], "account_id": account["id"], "amount": "1.00"},
    )
    assert response.status_code == 400


def test_record_amount_must_be_positive(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    response = client.post(
        "/api/finance-records",
        headers=auth_headers(token),
        json={"type": "income", "category_id": category["id"], "account_id": account["id"], "amount": "0.00"},
    )
    assert response.status_code == 422


def test_void_income_record_decreases_account_balance(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    record = create_record(client, token, "income", category["id"], account["id"], "30.00")
    response = client.post(f"/api/finance-records/{record['id']}/void", headers=auth_headers(token), json={"reason": "录入错误"})
    assert response.status_code == 200
    assert get_account(client, token, account["id"])["current_balance"] == "0.00"


def test_void_expense_record_increases_account_balance(client: TestClient) -> None:
    token = login(client)
    category = default_expense_category(client, token)
    account = default_account(client, token)
    record = create_record(client, token, "expense", category["id"], account["id"], "10.00")
    client.post(f"/api/finance-records/{record['id']}/void", headers=auth_headers(token), json={"reason": "录入错误"})
    assert get_account(client, token, account["id"])["current_balance"] == "0.00"


def test_void_record_sets_status_to_voided(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    record = create_record(client, token, "income", category["id"], account["id"])
    response = client.post(f"/api/finance-records/{record['id']}/void", headers=auth_headers(token), json={"reason": "录入错误"})
    assert response.json()["status"] == "voided"


def test_voided_record_cannot_be_voided_again(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    record = create_record(client, token, "income", category["id"], account["id"])
    client.post(f"/api/finance-records/{record['id']}/void", headers=auth_headers(token), json={"reason": "录入错误"})
    response = client.post(f"/api/finance-records/{record['id']}/void", headers=auth_headers(token), json={"reason": "再次作废"})
    assert response.status_code == 400


def test_finance_record_list_supports_pagination(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    for index in range(3):
        create_record(client, token, "income", category["id"], account["id"], "1.00", f"分页流水{index}")
    response = client.get("/api/finance-records?page=1&page_size=2", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2


def test_finance_record_list_supports_keyword_search(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    create_record(client, token, "income", category["id"], account["id"], "1.00", "杭州收入")
    response = client.get("/api/finance-records?keyword=杭州", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_finance_record_list_supports_type_filter(client: TestClient) -> None:
    token = login(client)
    income_category = default_income_category(client, token)
    expense_category = default_expense_category(client, token)
    account = default_account(client, token)
    create_record(client, token, "income", income_category["id"], account["id"], "1.00")
    create_record(client, token, "expense", expense_category["id"], account["id"], "1.00")
    response = client.get("/api/finance-records?type=expense", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["type"] == "expense"


def test_finance_record_list_supports_account_filter(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    default = default_account(client, token)
    another = create_account(client, token, "筛选账户")
    create_record(client, token, "income", category["id"], default["id"], "1.00")
    create_record(client, token, "income", category["id"], another["id"], "1.00")
    response = client.get(f"/api/finance-records?account_id={another['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["account_id"] == another["id"]


def test_money_fields_use_numeric_and_serialize_safely(client: TestClient) -> None:
    token = login(client)
    category = default_income_category(client, token)
    account = default_account(client, token)
    record = create_record(client, token, "income", category["id"], account["id"], "12.34")
    assert isinstance(inspect(FinanceRecord).columns.amount.type, Numeric)
    assert isinstance(inspect(FinanceAccount).columns.current_balance.type, Numeric)
    assert record["amount"] == "12.34"
    assert Decimal(record["amount"]) == Decimal("12.34")
