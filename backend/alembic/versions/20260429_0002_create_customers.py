"""create customer categories and customers

Revision ID: 20260429_0002
Revises: 20260429_0001
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260429_0002"
down_revision: str | None = "20260429_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_categories_id", "customer_categories", ["id"], unique=False)
    op.create_index("ix_customer_categories_deleted_at", "customer_categories", ["deleted_at"], unique=False)
    op.create_index(
        "uq_customer_categories_name_active",
        "customer_categories",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "customers",
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
        sa.Column("opening_receivable", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("current_receivable", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("credit_limit", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["customer_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customers_id", "customers", ["id"], unique=False)
    op.create_index("ix_customers_code", "customers", ["code"], unique=False)
    op.create_index("ix_customers_name", "customers", ["name"], unique=False)
    op.create_index("ix_customers_phone", "customers", ["phone"], unique=False)
    op.create_index("ix_customers_category_id", "customers", ["category_id"], unique=False)
    op.create_index("ix_customers_deleted_at", "customers", ["deleted_at"], unique=False)
    op.create_index(
        "uq_customers_name_active",
        "customers",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.execute(
        sa.text(
            "INSERT INTO customer_categories (name, sort_order, is_default) VALUES ('默认分类', 0, 1)"
        )
    )


def downgrade() -> None:
    op.drop_index("uq_customers_name_active", table_name="customers")
    op.drop_index("ix_customers_deleted_at", table_name="customers")
    op.drop_index("ix_customers_category_id", table_name="customers")
    op.drop_index("ix_customers_phone", table_name="customers")
    op.drop_index("ix_customers_name", table_name="customers")
    op.drop_index("ix_customers_code", table_name="customers")
    op.drop_index("ix_customers_id", table_name="customers")
    op.drop_table("customers")
    op.drop_index("uq_customer_categories_name_active", table_name="customer_categories")
    op.drop_index("ix_customer_categories_deleted_at", table_name="customer_categories")
    op.drop_index("ix_customer_categories_id", table_name="customer_categories")
    op.drop_table("customer_categories")
