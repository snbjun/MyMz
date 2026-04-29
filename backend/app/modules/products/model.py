from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, and_, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductCategory(Base):
    """第 5 阶段新增：产品分类，支持默认项和软删除。"""

    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    products: Mapped[list["Product"]] = relationship(back_populates="category")
    __table_args__ = (
        Index("uq_product_categories_name_active", "name", unique=True, sqlite_where=deleted_at.is_(None)),
        Index("ix_product_categories_deleted_at", "deleted_at"),
    )


class ProductUnit(Base):
    """第 5 阶段新增：产品单位，支持默认项和软删除。"""

    __tablename__ = "product_units"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    products: Mapped[list["Product"]] = relationship(back_populates="unit")
    __table_args__ = (
        Index("uq_product_units_name_active", "name", unique=True, sqlite_where=deleted_at.is_(None)),
        Index("ix_product_units_deleted_at", "deleted_at"),
    )


class Product(Base):
    """第 5 阶段新增：产品档案，不包含库存数量和库存流水。"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str | None] = mapped_column(String(64))
    barcode: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"))
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("product_units.id"))
    spec: Mapped[str | None] = mapped_column(String(128))
    model: Mapped[str | None] = mapped_column(String(128))
    brand: Mapped[str | None] = mapped_column(String(128))
    origin: Mapped[str | None] = mapped_column(String(128))
    sale_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    wholesale_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    stock_warning_qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    image_url: Mapped[str | None] = mapped_column(String(255))
    remark: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    category: Mapped[ProductCategory | None] = relationship(back_populates="products")
    unit: Mapped[ProductUnit | None] = relationship(back_populates="products")
    __table_args__ = (
        Index("ix_products_code", "code"),
        Index("ix_products_barcode", "barcode"),
        Index("ix_products_name", "name"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_unit_id", "unit_id"),
        Index("ix_products_deleted_at", "deleted_at"),
        Index("uq_products_name_active", "name", unique=True, sqlite_where=deleted_at.is_(None)),
        Index(
            "uq_products_code_active",
            "code",
            unique=True,
            sqlite_where=and_(deleted_at.is_(None), code.is_not(None), code != ""),
        ),
        Index(
            "uq_products_barcode_active",
            "barcode",
            unique=True,
            sqlite_where=and_(deleted_at.is_(None), barcode.is_not(None), barcode != ""),
        ),
    )
