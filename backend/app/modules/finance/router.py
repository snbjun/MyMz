from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.permissions import Permission, require_permission
from app.modules.audit_logs.service import record_audit_log
from app.modules.finance.schemas import (
    FinanceAccountCreate,
    FinanceAccountRead,
    FinanceAccountUpdate,
    FinanceCategoryCreate,
    FinanceCategoryRead,
    FinanceCategoryUpdate,
    FinanceRecordCreate,
    FinanceRecordListResponse,
    FinanceRecordRead,
    FinanceRecordVoid,
    SuccessResponse,
)
from app.modules.finance.service import FinanceService
from app.modules.users.model import User

router = APIRouter()


@router.get("/finance-categories", response_model=list[FinanceCategoryRead])
def list_finance_categories(
    type: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FinanceCategoryRead]:
    return FinanceService(db).list_categories(type, is_active)


@router.post("/finance-categories", response_model=FinanceCategoryRead)
def create_finance_category(
    payload: FinanceCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceCategoryRead:
    category = FinanceService(db).create_category(payload)
    record_audit_log(db, current_user, "finance", "create_category", f"创建收支分类：{category.name}", "finance_category", category.id, category.name, request)
    return category


@router.put("/finance-categories/{category_id}", response_model=FinanceCategoryRead)
def update_finance_category(
    category_id: int,
    payload: FinanceCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceCategoryRead:
    category = FinanceService(db).update_category(category_id, payload)
    record_audit_log(db, current_user, "finance", "update_category", f"编辑收支分类：{category.name}", "finance_category", category.id, category.name, request)
    return category


@router.delete("/finance-categories/{category_id}", response_model=SuccessResponse)
def delete_finance_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> SuccessResponse:
    FinanceService(db).delete_category(category_id)
    record_audit_log(db, current_user, "finance", "delete_category", f"删除收支分类：{category_id}", "finance_category", category_id, str(category_id), request)
    return SuccessResponse()


@router.post("/finance-categories/{category_id}/toggle-active", response_model=FinanceCategoryRead)
def toggle_finance_category_active(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceCategoryRead:
    category = FinanceService(db).toggle_category_active(category_id)
    record_audit_log(db, current_user, "finance", "toggle_category", f"启用禁用收支分类：{category.name}", "finance_category", category.id, category.name, request)
    return category


@router.get("/finance-accounts", response_model=list[FinanceAccountRead])
def list_finance_accounts(
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FinanceAccountRead]:
    return FinanceService(db).list_accounts(is_active)


@router.post("/finance-accounts", response_model=FinanceAccountRead)
def create_finance_account(
    payload: FinanceAccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceAccountRead:
    account = FinanceService(db).create_account(payload)
    record_audit_log(db, current_user, "finance", "create_account", f"创建资金账户：{account.name}", "finance_account", account.id, account.name, request)
    return account


@router.get("/finance-accounts/{account_id}", response_model=FinanceAccountRead)
def get_finance_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinanceAccountRead:
    return FinanceService(db).get_account(account_id)


@router.put("/finance-accounts/{account_id}", response_model=FinanceAccountRead)
def update_finance_account(
    account_id: int,
    payload: FinanceAccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceAccountRead:
    account = FinanceService(db).update_account(account_id, payload)
    record_audit_log(db, current_user, "finance", "update_account", f"编辑资金账户：{account.name}", "finance_account", account.id, account.name, request)
    return account


@router.delete("/finance-accounts/{account_id}", response_model=SuccessResponse)
def delete_finance_account(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> SuccessResponse:
    FinanceService(db).delete_account(account_id)
    record_audit_log(db, current_user, "finance", "delete_account", f"删除资金账户：{account_id}", "finance_account", account_id, str(account_id), request)
    return SuccessResponse()


@router.post("/finance-accounts/{account_id}/toggle-active", response_model=FinanceAccountRead)
def toggle_finance_account_active(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceAccountRead:
    account = FinanceService(db).toggle_account_active(account_id)
    record_audit_log(db, current_user, "finance", "toggle_account", f"启用禁用资金账户：{account.name}", "finance_account", account.id, account.name, request)
    return account


@router.get("/finance-records", response_model=FinanceRecordListResponse)
def list_finance_records(
    keyword: str | None = None,
    type: str | None = None,
    category_id: int | None = None,
    account_id: int | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinanceRecordListResponse:
    return FinanceService(db).list_records(
        keyword, type, category_id, account_id, status, start_date, end_date, page, page_size
    )


@router.post("/finance-records", response_model=FinanceRecordRead)
def create_finance_record(
    payload: FinanceRecordCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceRecordRead:
    record = FinanceService(db).create_record(payload, current_user)
    record_audit_log(db, current_user, "finance", "create_record", f"新增收支流水：{record.record_no}", "finance_record", record.id, record.record_no, request)
    return record


@router.get("/finance-records/{record_id}", response_model=FinanceRecordRead)
def get_finance_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinanceRecordRead:
    return FinanceService(db).get_record(record_id)


@router.post("/finance-records/{record_id}/void", response_model=FinanceRecordRead)
def void_finance_record(
    record_id: int,
    payload: FinanceRecordVoid,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_MANAGE)),
) -> FinanceRecordRead:
    record = FinanceService(db).void_record(record_id, payload, current_user)
    record_audit_log(db, current_user, "finance", "void_record", f"作废收支流水：{record.record_no}", "finance_record", record.id, record.record_no, request)
    return record
