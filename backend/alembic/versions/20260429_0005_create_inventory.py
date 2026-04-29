"""create inventory tables

Revision ID: 20260429_0005
Revises: 20260429_0004
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260429_0005"
down_revision: str | None = "20260429_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_warehouses_id", "warehouses", ["id"], unique=False)
    op.create_index("ix_warehouses_deleted_at", "warehouses", ["deleted_at"], unique=False)
    op.create_index("ix_warehouses_is_active", "warehouses", ["is_active"], unique=False)

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(18, 3), server_default="0", nullable=False),
        sa.Column("average_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("total_cost", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
    )
    op.create_index("ix_inventory_id", "inventory", ["id"], unique=False)
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"], unique=False)
    op.create_index("ix_inventory_warehouse_id", "inventory", ["warehouse_id"], unique=False)

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("movement_no", sa.String(length=64), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("before_qty", sa.Numeric(18, 3), server_default="0", nullable=False),
        sa.Column("after_qty", sa.Numeric(18, 3), server_default="0", nullable=False),
        sa.Column("before_avg_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("after_avg_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("movement_no"),
    )
    op.create_index("ix_stock_movements_id", "stock_movements", ["id"], unique=False)
    op.create_index("ix_stock_movements_movement_no", "stock_movements", ["movement_no"], unique=False)
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"], unique=False)
    op.create_index("ix_stock_movements_warehouse_id", "stock_movements", ["warehouse_id"], unique=False)
    op.create_index("ix_stock_movements_type", "stock_movements", ["movement_type"], unique=False)
    op.create_index("ix_stock_movements_direction", "stock_movements", ["direction"], unique=False)
    op.create_index("ix_stock_movements_created_at", "stock_movements", ["created_at"], unique=False)
    op.create_index("ix_stock_movements_source", "stock_movements", ["source_type", "source_id"], unique=False)

    op.execute(sa.text("INSERT INTO warehouses (name, sort_order, is_default, is_active) VALUES ('默认仓库', 0, 1, 1)"))


def downgrade() -> None:
    op.drop_index("ix_stock_movements_source", table_name="stock_movements")
    op.drop_index("ix_stock_movements_created_at", table_name="stock_movements")
    op.drop_index("ix_stock_movements_direction", table_name="stock_movements")
    op.drop_index("ix_stock_movements_type", table_name="stock_movements")
    op.drop_index("ix_stock_movements_warehouse_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_movement_no", table_name="stock_movements")
    op.drop_index("ix_stock_movements_id", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("ix_inventory_warehouse_id", table_name="inventory")
    op.drop_index("ix_inventory_product_id", table_name="inventory")
    op.drop_index("ix_inventory_id", table_name="inventory")
    op.drop_table("inventory")
    op.drop_index("ix_warehouses_is_active", table_name="warehouses")
    op.drop_index("ix_warehouses_deleted_at", table_name="warehouses")
    op.drop_index("ix_warehouses_id", table_name="warehouses")
    op.drop_table("warehouses")
