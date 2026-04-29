from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.products.model import Product
from app.modules.users.model import User


class Warehouse(Base):
    """第 6 阶段新增：仓库主表，第一版只初始化默认仓库。"""

    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    inventory_items: Mapped[list["Inventory"]] = relationship(back_populates="warehouse")
    stock_movements: Mapped[list["StockMovement"]] = relationship(back_populates="warehouse")

    __table_args__ = (
        Index("ix_warehouses_deleted_at", "deleted_at"),
        Index("ix_warehouses_is_active", "is_active"),
    )


class Inventory(Base):
    """第 6 阶段新增：当前库存余额，只能由库存服务更新。"""

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    product: Mapped[Product] = relationship()
    warehouse: Mapped[Warehouse] = relationship(back_populates="inventory_items")

    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
        Index("ix_inventory_product_id", "product_id"),
        Index("ix_inventory_warehouse_id", "warehouse_id"),
    )


class StockMovement(Base):
    """第 6 阶段新增：库存流水原则上不可修改、不可删除。"""

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movement_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    before_qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    after_qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    before_avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    after_avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer)
    remark: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    product: Mapped[Product] = relationship()
    warehouse: Mapped[Warehouse] = relationship(back_populates="stock_movements")
    created_by: Mapped[User | None] = relationship()

    __table_args__ = (
        Index("ix_stock_movements_movement_no", "movement_no"),
        Index("ix_stock_movements_product_id", "product_id"),
        Index("ix_stock_movements_warehouse_id", "warehouse_id"),
        Index("ix_stock_movements_type", "movement_type"),
        Index("ix_stock_movements_direction", "direction"),
        Index("ix_stock_movements_created_at", "created_at"),
        Index("ix_stock_movements_source", "source_type", "source_id"),
    )
