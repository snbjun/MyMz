from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.customers.model import Customer
from app.modules.inventory.model import Warehouse
from app.modules.products.model import Product
from app.modules.users.model import User


class SalesOrder(Base):
    """第 7 阶段新增：销售单主表，作废用状态记录，不物理删除。"""

    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_shipped")
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unpaid")
    total_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    receivable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
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

    customer: Mapped[Customer] = relationship()
    warehouse: Mapped[Warehouse] = relationship()
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    items: Mapped[list["SalesOrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="SalesOrderItem.id",
    )
    payments: Mapped[list["SalesPayment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="SalesPayment.id",
    )

    __table_args__ = (
        Index("ix_sales_orders_order_no", "order_no"),
        Index("ix_sales_orders_customer_id", "customer_id"),
        Index("ix_sales_orders_warehouse_id", "warehouse_id"),
        Index("ix_sales_orders_status", "status"),
        Index("ix_sales_orders_order_date", "order_date"),
    )


class SalesOrderItem(Base):
    """第 7 阶段新增：销售单明细，冗余保存产品快照字段。"""

    __tablename__ = "sales_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product_barcode: Mapped[str | None] = mapped_column(String(64))
    product_spec: Mapped[str | None] = mapped_column(String(128))
    product_model: Mapped[str | None] = mapped_column(String(128))
    unit_name: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    shipped_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False, default=Decimal("0.000"))
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

    order: Mapped[SalesOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    __table_args__ = (
        Index("ix_sales_order_items_order_id", "sales_order_id"),
        Index("ix_sales_order_items_product_id", "product_id"),
    )


class SalesPayment(Base):
    """第 7 阶段新增：销售收款记录，第一版不可编辑、不可删除。"""

    __tablename__ = "sales_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    payment_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False, default="cash")
    remark: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    order: Mapped[SalesOrder] = relationship(back_populates="payments")
    created_by: Mapped[User | None] = relationship()

    __table_args__ = (
        Index("ix_sales_payments_order_id", "sales_order_id"),
        Index("ix_sales_payments_payment_no", "payment_no"),
        Index("ix_sales_payments_payment_date", "payment_date"),
    )
