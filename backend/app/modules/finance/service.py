from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.finance.model import FinanceAccount, FinanceCategory, FinanceRecord
from app.modules.finance.repository import FinanceRepository
from app.modules.finance.schemas import (
    FinanceAccountCreate,
    FinanceAccountUpdate,
    FinanceCategoryCreate,
    FinanceCategoryUpdate,
    FinanceRecordCreate,
    FinanceRecordListResponse,
    FinanceRecordVoid,
)
from app.modules.users.model import User

MONEY = Decimal("0.01")
ZERO = Decimal("0.00")


class FinanceService:
    """第 9 阶段新增：收支分类、资金账户和流水的业务规则与事务。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FinanceRepository(db)

    def list_categories(self, category_type: str | None, is_active: bool | None) -> list[FinanceCategory]:
        return self.repo.list_categories(category_type, is_active)

    def create_category(self, payload: FinanceCategoryCreate) -> FinanceCategory:
        if self.repo.get_category_by_name_and_type(payload.name, payload.type):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="同一类型下分类名称已存在")
        if payload.is_default:
            self._clear_default_categories(payload.type)
        category = FinanceCategory(**payload.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category_id: int, payload: FinanceCategoryUpdate) -> FinanceCategory:
        category = self._get_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        target_type = data.get("type", category.type)
        target_name = data.get("name", category.name)
        if self.repo.has_other_category(target_name, target_type, category_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="同一类型下分类名称已存在")
        if category.is_default and data.get("is_default") is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消默认分类")
        if data.get("is_default") is True:
            self._clear_default_categories(target_type, exclude_category_id=category_id)
        if category.is_default and "type" in data and data["type"] != category.type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认分类不能修改类型")
        for field, value in data.items():
            setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self._get_category(category_id)
        if category.is_default or self.repo.count_active_categories(category.type, category_id) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除默认分类")
        if self.repo.count_records_by_category(category_id, normal_only=True) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类正在被正常流水使用，不能删除")
        self.repo.soft_delete_category(category)
        self.db.commit()

    def toggle_category_active(self, category_id: int) -> FinanceCategory:
        category = self._get_category(category_id)
        if category.is_default and category.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认分类不能禁用")
        category.is_active = not category.is_active
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_accounts(self, is_active: bool | None) -> list[FinanceAccount]:
        return self.repo.list_accounts(is_active)

    def get_account(self, account_id: int) -> FinanceAccount:
        account = self.repo.get_account(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资金账户不存在或已删除")
        return account

    def create_account(self, payload: FinanceAccountCreate) -> FinanceAccount:
        if self.repo.get_account_by_name(payload.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账户名称已存在")
        if payload.is_default:
            self._clear_default_accounts()
        opening_balance = self._money(payload.opening_balance)
        account = FinanceAccount(
            name=payload.name,
            type=payload.type,
            opening_balance=opening_balance,
            current_balance=opening_balance,
            sort_order=payload.sort_order,
            is_default=payload.is_default,
            is_active=payload.is_active,
            remark=payload.remark,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def update_account(self, account_id: int, payload: FinanceAccountUpdate) -> FinanceAccount:
        account = self.get_account(account_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and self.repo.has_other_account(data["name"], account_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账户名称已存在")
        if "opening_balance" in data:
            if self.repo.count_records_by_account(account_id) > 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账户已有流水，不能修改期初余额")
            opening_balance = self._money(data["opening_balance"])
            account.opening_balance = opening_balance
            account.current_balance = opening_balance
            data.pop("opening_balance")
        if data.get("is_default") is True:
            self._clear_default_accounts(exclude_account_id=account_id)
        if account.is_default and data.get("is_default") is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消默认账户")
        if account.is_default and data.get("is_active") is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认账户不能禁用")
        if data.get("is_active") is False and self.repo.count_active_accounts(account_id) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少需要保留一个启用账户")
        for field, value in data.items():
            setattr(account, field, value)
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: int) -> None:
        account = self.get_account(account_id)
        if account.is_default:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认账户不能删除")
        if self.repo.count_records_by_account(account_id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账户已有流水，不能删除")
        self.repo.soft_delete_account(account)
        self.db.commit()

    def toggle_account_active(self, account_id: int) -> FinanceAccount:
        account = self.get_account(account_id)
        if account.is_default and account.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认账户不能禁用")
        if account.is_active and self.repo.count_active_accounts(account_id) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少需要保留一个启用账户")
        account.is_active = not account.is_active
        self.db.commit()
        self.db.refresh(account)
        return account

    def list_records(
        self,
        keyword: str | None,
        record_type: str | None,
        category_id: int | None,
        account_id: int | None,
        status_value: str | None,
        start_date,
        end_date,
        page: int,
        page_size: int,
    ) -> FinanceRecordListResponse:
        records, total = self.repo.list_records(
            keyword, record_type, category_id, account_id, status_value, start_date, end_date, page, page_size
        )
        return FinanceRecordListResponse(items=records, total=total, page=page, page_size=page_size)

    def get_record(self, record_id: int) -> FinanceRecord:
        record = self.repo.get_record(record_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收支流水不存在")
        return record

    def create_record(self, payload: FinanceRecordCreate, current_user: User) -> FinanceRecord:
        category = self._get_category(payload.category_id)
        account = self.get_account(payload.account_id)
        self._ensure_category_available(category, payload.type)
        self._ensure_account_available(account)
        amount = self._money(payload.amount)
        try:
            record = FinanceRecord(
                record_no=self.repo.next_record_no(payload.type),
                type=payload.type,
                record_date=payload.record_date,
                category_id=category.id,
                account_id=account.id,
                amount=amount,
                counterparty_type=payload.counterparty_type,
                counterparty_id=payload.counterparty_id,
                summary=payload.summary,
                remark=payload.remark,
                status="normal",
                created_by_id=current_user.id,
            )
            self._apply_balance(account, payload.type, amount)
            self.db.add(record)
            self.db.commit()
            return self.get_record(record.id)
        except Exception:
            self.db.rollback()
            raise

    def void_record(self, record_id: int, payload: FinanceRecordVoid, current_user: User) -> FinanceRecord:
        record = self.get_record(record_id)
        if record.status != "normal":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有正常流水可以作废")
        try:
            if record.type == "income":
                record.account.current_balance = self._money(record.account.current_balance - record.amount)
            else:
                record.account.current_balance = self._money(record.account.current_balance + record.amount)
            record.status = "voided"
            record.voided_by_id = current_user.id
            record.voided_at = datetime.now(timezone.utc)
            record.void_reason = payload.reason
            self.db.commit()
            return self.get_record(record.id)
        except Exception:
            self.db.rollback()
            raise

    def _get_category(self, category_id: int) -> FinanceCategory:
        category = self.repo.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收支分类不存在或已删除")
        return category

    def _ensure_category_available(self, category: FinanceCategory, record_type: str) -> None:
        if not category.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类已禁用，不能新增流水")
        if category.type != record_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类类型与流水类型不匹配")

    def _ensure_account_available(self, account: FinanceAccount) -> None:
        if not account.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账户已禁用，不能新增流水")

    def _apply_balance(self, account: FinanceAccount, record_type: str, amount: Decimal) -> None:
        if record_type == "income":
            account.current_balance = self._money(account.current_balance + amount)
        else:
            account.current_balance = self._money(account.current_balance - amount)

    def _clear_default_categories(self, category_type: str, exclude_category_id: int | None = None) -> None:
        for category in self.repo.list_categories(category_type, None):
            if exclude_category_id is None or category.id != exclude_category_id:
                category.is_default = False

    def _clear_default_accounts(self, exclude_account_id: int | None = None) -> None:
        for account in self.repo.list_accounts(None):
            if exclude_account_id is None or account.id != exclude_account_id:
                account.is_default = False

    def _money(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)
