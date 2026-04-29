"""create sales order tables

Revision ID: 20260430_0006
Revises: 20260429_0005
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260430_0006"
down_revision: str | None = "20260429_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="draft", nullable=False),
        sa.Column("delivery_status", sa.String(length=32), server_default="not_shipped", nullable=False),
        sa.Column("payment_status", sa.String(length=32), server_default="unpaid", nullable=False),
        sa.Column("total_quantity", sa.Numeric(18, 3), server_default="0", nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("receivable_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("paid_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("unpaid_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("confirmed_by_id", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by_id", sa.Integer(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["cancelled_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["confirmed_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
    )
    op.create_index("ix_sales_orders_id", "sales_orders", ["id"], unique=False)
    op.create_index("ix_sales_orders_order_no", "sales_orders", ["order_no"], unique=False)
    op.create_index("ix_sales_orders_customer_id", "sales_orders", ["customer_id"], unique=False)
    op.create_index("ix_sales_orders_warehouse_id", "sales_orders", ["warehouse_id"], unique=False)
    op.create_index("ix_sales_orders_status", "sales_orders", ["status"], unique=False)
    op.create_index("ix_sales_orders_order_date", "sales_orders", ["order_date"], unique=False)

    op.create_table(
        "sales_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=True),
        sa.Column("product_name", sa.String(length=128), nullable=False),
        sa.Column("product_barcode", sa.String(length=64), nullable=True),
        sa.Column("product_spec", sa.String(length=128), nullable=True),
        sa.Column("product_model", sa.String(length=128), nullable=True),
        sa.Column("unit_name", sa.String(length=64), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.Column("shipped_quantity", sa.Numeric(18, 3), server_default="0", nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("line_amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_order_items_id", "sales_order_items", ["id"], unique=False)
    op.create_index("ix_sales_order_items_order_id", "sales_order_items", ["sales_order_id"], unique=False)
    op.create_index("ix_sales_order_items_product_id", "sales_order_items", ["product_id"], unique=False)

    op.create_table(
        "sales_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("payment_no", sa.String(length=64), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("method", sa.String(length=32), server_default="cash", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_no"),
    )
    op.create_index("ix_sales_payments_id", "sales_payments", ["id"], unique=False)
    op.create_index("ix_sales_payments_order_id", "sales_payments", ["sales_order_id"], unique=False)
    op.create_index("ix_sales_payments_payment_no", "sales_payments", ["payment_no"], unique=False)
    op.create_index("ix_sales_payments_payment_date", "sales_payments", ["payment_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sales_payments_payment_date", table_name="sales_payments")
    op.drop_index("ix_sales_payments_payment_no", table_name="sales_payments")
    op.drop_index("ix_sales_payments_order_id", table_name="sales_payments")
    op.drop_index("ix_sales_payments_id", table_name="sales_payments")
    op.drop_table("sales_payments")
    op.drop_index("ix_sales_order_items_product_id", table_name="sales_order_items")
    op.drop_index("ix_sales_order_items_order_id", table_name="sales_order_items")
    op.drop_index("ix_sales_order_items_id", table_name="sales_order_items")
    op.drop_table("sales_order_items")
    op.drop_index("ix_sales_orders_order_date", table_name="sales_orders")
    op.drop_index("ix_sales_orders_status", table_name="sales_orders")
    op.drop_index("ix_sales_orders_warehouse_id", table_name="sales_orders")
    op.drop_index("ix_sales_orders_customer_id", table_name="sales_orders")
    op.drop_index("ix_sales_orders_order_no", table_name="sales_orders")
    op.drop_index("ix_sales_orders_id", table_name="sales_orders")
    op.drop_table("sales_orders")
