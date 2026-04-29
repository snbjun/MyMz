from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SupplierCategory(Base):
    """第 4 阶段新增：供应商分类，支持软删除和默认分类。"""

    __tablename__ = "supplier_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    suppliers: Mapped[list["Supplier"]] = relationship(back_populates="category")
    __table_args__ = (
        Index(
            "uq_supplier_categories_name_active",
            "name",
            unique=True,
            sqlite_where=deleted_at.is_(None),
        ),
        Index("ix_supplier_categories_deleted_at", "deleted_at"),
    )


class Supplier(Base):
    """第 4 阶段新增：供应商资料，金额字段统一使用 Numeric/Decimal。"""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_categories.id"))
    contact_name: Mapped[str | None] = mapped_column(String(64))
    phone: Mapped[str | None] = mapped_column(String(32))
    backup_phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(128))
    wechat: Mapped[str | None] = mapped_column(String(64))
    address: Mapped[str | None] = mapped_column(String(255))
    tax_number: Mapped[str | None] = mapped_column(String(64))
    opening_payable: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    current_payable: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    remark: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    category: Mapped[SupplierCategory | None] = relationship(back_populates="suppliers")
    __table_args__ = (
        Index("ix_suppliers_code", "code"),
        Index("ix_suppliers_name", "name"),
        Index(
            "uq_suppliers_name_active",
            "name",
            unique=True,
            sqlite_where=deleted_at.is_(None),
        ),
        Index("ix_suppliers_phone", "phone"),
        Index("ix_suppliers_category_id", "category_id"),
        Index("ix_suppliers_deleted_at", "deleted_at"),
    )

