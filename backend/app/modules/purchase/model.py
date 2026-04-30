from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.suppliers.model import Supplier
from app.modules.inventory.model import Warehouse
from app.modules.products.model import Product
from app.modules.users.model import User


class PurchaseOrder(Base):
    """第 8 阶段新增：采购单主表，作废用状态记录，不物理删除。"""

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    receive_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_received")
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unpaid")
    total_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    payable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    unpaid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    remark: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    confirmed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    supplier: Mapped[Supplier] = relationship()
    warehouse: Mapped[Warehouse] = relationship()
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    items: Mapped[list["PurchaseOrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderItem.id",
    )
    payments: Mapped[list["PurchasePayment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="PurchasePayment.id",
    )

    __table_args__ = (
        Index("ix_purchase_orders_order_no", "order_no"),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_warehouse_id", "warehouse_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
    )


class PurchaseOrderItem(Base):
    """第 8 阶段新增：采购单明细，冗余保存产品快照字段。"""

    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product_barcode: Mapped[str | None] = mapped_column(String(64))
    product_spec: Mapped[str | None] = mapped_column(String(128))
    product_model: Mapped[str | None] = mapped_column(String(128))
    unit_name: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    line_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    __table_args__ = (
        Index("ix_purchase_order_items_order_id", "purchase_order_id"),
        Index("ix_purchase_order_items_product_id", "product_id"),
    )


class PurchasePayment(Base):
    """第 8 阶段新增：采购付款记录，第一版不可编辑、不可删除。"""

    __tablename__ = "purchase_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    payment_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False, default="cash")
    remark: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    order: Mapped[PurchaseOrder] = relationship(back_populates="payments")
    created_by: Mapped[User | None] = relationship()

    __table_args__ = (
        Index("ix_purchase_payments_order_id", "purchase_order_id"),
        Index("ix_purchase_payments_payment_no", "payment_no"),
        Index("ix_purchase_payments_payment_date", "payment_date"),
    )
