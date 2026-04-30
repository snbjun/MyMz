from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.users.model import User


class FinanceCategory(Base):
    """第 9 阶段新增：收支分类，按收入/支出类型分别维护。"""

    __tablename__ = "finance_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_finance_categories_type", "type"),
        Index("ix_finance_categories_name", "name"),
    )


class FinanceAccount(Base):
    """第 9 阶段新增：资金账户，余额只能由账户初始化和收支流水更新。"""

    __tablename__ = "finance_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="cash")
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_finance_accounts_name", "name"),
        Index("ix_finance_accounts_type", "type"),
    )


class FinanceRecord(Base):
    """第 9 阶段新增：收支流水不物理删除，作废用状态并反向更新账户余额。"""

    __tablename__ = "finance_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    record_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("finance_categories.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("finance_accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    counterparty_type: Mapped[str | None] = mapped_column(String(32))
    counterparty_id: Mapped[int | None] = mapped_column()
    summary: Mapped[str | None] = mapped_column(String(255))
    remark: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    voided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    void_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped[FinanceCategory] = relationship()
    account: Mapped[FinanceAccount] = relationship()
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    voided_by: Mapped[User | None] = relationship(foreign_keys=[voided_by_id])

    __table_args__ = (
        Index("ix_finance_records_record_no", "record_no"),
        Index("ix_finance_records_type", "type"),
        Index("ix_finance_records_status", "status"),
        Index("ix_finance_records_record_date", "record_date"),
        Index("ix_finance_records_category_id", "category_id"),
        Index("ix_finance_records_account_id", "account_id"),
    )
