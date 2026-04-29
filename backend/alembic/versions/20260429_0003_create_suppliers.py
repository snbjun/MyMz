"""create supplier categories and suppliers

Revision ID: 20260429_0003
Revises: 20260429_0002
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260429_0003"
down_revision: str | None = "20260429_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "supplier_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supplier_categories_id", "supplier_categories", ["id"], unique=False)
    op.create_index("ix_supplier_categories_deleted_at", "supplier_categories", ["deleted_at"], unique=False)
    op.create_index(
        "uq_supplier_categories_name_active",
        "supplier_categories",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("contact_name", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("backup_phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("wechat", sa.String(length=64), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("tax_number", sa.String(length=64), nullable=True),
        sa.Column("opening_payable", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("current_payable", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("credit_limit", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["supplier_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suppliers_id", "suppliers", ["id"], unique=False)
    op.create_index("ix_suppliers_code", "suppliers", ["code"], unique=False)
    op.create_index("ix_suppliers_name", "suppliers", ["name"], unique=False)
    op.create_index("ix_suppliers_phone", "suppliers", ["phone"], unique=False)
    op.create_index("ix_suppliers_category_id", "suppliers", ["category_id"], unique=False)
    op.create_index("ix_suppliers_deleted_at", "suppliers", ["deleted_at"], unique=False)
    op.create_index(
        "uq_suppliers_name_active",
        "suppliers",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.execute(
        sa.text(
            "INSERT INTO supplier_categories (name, sort_order, is_default) VALUES ('默认分类', 0, 1)"
        )
    )


def downgrade() -> None:
    op.drop_index("uq_suppliers_name_active", table_name="suppliers")
    op.drop_index("ix_suppliers_deleted_at", table_name="suppliers")
    op.drop_index("ix_suppliers_category_id", table_name="suppliers")
    op.drop_index("ix_suppliers_phone", table_name="suppliers")
    op.drop_index("ix_suppliers_name", table_name="suppliers")
    op.drop_index("ix_suppliers_code", table_name="suppliers")
    op.drop_index("ix_suppliers_id", table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_index("uq_supplier_categories_name_active", table_name="supplier_categories")
    op.drop_index("ix_supplier_categories_deleted_at", table_name="supplier_categories")
    op.drop_index("ix_supplier_categories_id", table_name="supplier_categories")
    op.drop_table("supplier_categories")
