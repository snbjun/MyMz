from datetime import date, datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.finance.model import FinanceAccount, FinanceCategory, FinanceRecord


class FinanceRepository:
    """第 9 阶段新增：费用收入模块数据库读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def next_record_no(self, record_type: str) -> str:
        prefix_name = "SR" if record_type == "income" else "ZC"
        prefix = f"{prefix_name}{datetime.now():%Y%m%d}"
        last_no = self.db.scalar(
            select(FinanceRecord.record_no)
            .where(FinanceRecord.record_no.like(f"{prefix}%"))
            .order_by(FinanceRecord.record_no.desc())
            .limit(1)
        )
        seq = int(last_no[-4:]) + 1 if last_no else 1
        return f"{prefix}{seq:04d}"

    def list_categories(self, category_type: str | None, is_active: bool | None) -> list[FinanceCategory]:
        stmt = select(FinanceCategory).where(FinanceCategory.deleted_at.is_(None))
        if category_type:
            stmt = stmt.where(FinanceCategory.type == category_type)
        if is_active is not None:
            stmt = stmt.where(FinanceCategory.is_active.is_(is_active))
        stmt = stmt.order_by(FinanceCategory.type.asc(), FinanceCategory.sort_order.asc(), FinanceCategory.id.asc())
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: int) -> FinanceCategory | None:
        return self.db.scalar(
            select(FinanceCategory).where(FinanceCategory.id == category_id, FinanceCategory.deleted_at.is_(None))
        )

    def get_category_by_name_and_type(self, name: str, category_type: str) -> FinanceCategory | None:
        return self.db.scalar(
            select(FinanceCategory).where(
                FinanceCategory.name == name,
                FinanceCategory.type == category_type,
                FinanceCategory.deleted_at.is_(None),
            )
        )

    def has_other_category(self, name: str, category_type: str, category_id: int) -> bool:
        stmt = select(func.count()).select_from(FinanceCategory).where(
            FinanceCategory.name == name,
            FinanceCategory.type == category_type,
            FinanceCategory.id != category_id,
            FinanceCategory.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def count_active_categories(self, category_type: str, exclude_category_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(FinanceCategory).where(
            FinanceCategory.type == category_type,
            FinanceCategory.deleted_at.is_(None),
            FinanceCategory.is_active.is_(True),
        )
        if exclude_category_id is not None:
            stmt = stmt.where(FinanceCategory.id != exclude_category_id)
        return int(self.db.scalar(stmt) or 0)

    def count_records_by_category(self, category_id: int, normal_only: bool = False) -> int:
        stmt = select(func.count()).select_from(FinanceRecord).where(FinanceRecord.category_id == category_id)
        if normal_only:
            stmt = stmt.where(FinanceRecord.status == "normal")
        return int(self.db.scalar(stmt) or 0)

    def list_accounts(self, is_active: bool | None) -> list[FinanceAccount]:
        stmt = select(FinanceAccount).where(FinanceAccount.deleted_at.is_(None))
        if is_active is not None:
            stmt = stmt.where(FinanceAccount.is_active.is_(is_active))
        stmt = stmt.order_by(FinanceAccount.sort_order.asc(), FinanceAccount.id.asc())
        return list(self.db.scalars(stmt).all())

    def get_account(self, account_id: int) -> FinanceAccount | None:
        return self.db.scalar(
            select(FinanceAccount).where(FinanceAccount.id == account_id, FinanceAccount.deleted_at.is_(None))
        )

    def get_account_by_name(self, name: str) -> FinanceAccount | None:
        return self.db.scalar(
            select(FinanceAccount).where(FinanceAccount.name == name, FinanceAccount.deleted_at.is_(None))
        )

    def has_other_account(self, name: str, account_id: int) -> bool:
        stmt = select(func.count()).select_from(FinanceAccount).where(
            FinanceAccount.name == name,
            FinanceAccount.id != account_id,
            FinanceAccount.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def count_active_accounts(self, exclude_account_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(FinanceAccount).where(
            FinanceAccount.deleted_at.is_(None),
            FinanceAccount.is_active.is_(True),
        )
        if exclude_account_id is not None:
            stmt = stmt.where(FinanceAccount.id != exclude_account_id)
        return int(self.db.scalar(stmt) or 0)

    def count_records_by_account(self, account_id: int) -> int:
        stmt = select(func.count()).select_from(FinanceRecord).where(FinanceRecord.account_id == account_id)
        return int(self.db.scalar(stmt) or 0)

    def list_records(
        self,
        keyword: str | None,
        record_type: str | None,
        category_id: int | None,
        account_id: int | None,
        status_value: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[FinanceRecord], int]:
        filters = []
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    FinanceRecord.record_no.like(like_keyword),
                    FinanceRecord.summary.like(like_keyword),
                    FinanceRecord.remark.like(like_keyword),
                )
            )
        if record_type:
            filters.append(FinanceRecord.type == record_type)
        if category_id is not None:
            filters.append(FinanceRecord.category_id == category_id)
        if account_id is not None:
            filters.append(FinanceRecord.account_id == account_id)
        if status_value:
            filters.append(FinanceRecord.status == status_value)
        if start_date:
            filters.append(FinanceRecord.record_date >= start_date)
        if end_date:
            filters.append(FinanceRecord.record_date <= end_date)
        where_clause = and_(*filters) if filters else True
        total = int(self.db.scalar(select(func.count()).select_from(FinanceRecord).where(where_clause)) or 0)
        stmt = (
            select(FinanceRecord)
            .options(joinedload(FinanceRecord.category), joinedload(FinanceRecord.account), joinedload(FinanceRecord.created_by))
            .where(where_clause)
            .order_by(FinanceRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def get_record(self, record_id: int) -> FinanceRecord | None:
        return self.db.scalar(
            select(FinanceRecord)
            .options(
                joinedload(FinanceRecord.category),
                joinedload(FinanceRecord.account),
                joinedload(FinanceRecord.created_by),
                joinedload(FinanceRecord.voided_by),
            )
            .where(FinanceRecord.id == record_id)
        )

    def soft_delete_category(self, category: FinanceCategory) -> None:
        category.deleted_at = datetime.now(timezone.utc)
        category.is_active = False

    def soft_delete_account(self, account: FinanceAccount) -> None:
        account.deleted_at = datetime.now(timezone.utc)
        account.is_active = False
