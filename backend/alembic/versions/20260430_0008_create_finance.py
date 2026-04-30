"""create finance tables

Revision ID: 20260430_0008
Revises: 20260430_0007
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260430_0008"
down_revision: str | None = "20260430_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "finance_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finance_categories_id", "finance_categories", ["id"], unique=False)
    op.create_index("ix_finance_categories_name", "finance_categories", ["name"], unique=False)
    op.create_index("ix_finance_categories_type", "finance_categories", ["type"], unique=False)

    op.create_table(
        "finance_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=32), server_default="cash", nullable=False),
        sa.Column("opening_balance", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("current_balance", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finance_accounts_id", "finance_accounts", ["id"], unique=False)
    op.create_index("ix_finance_accounts_name", "finance_accounts", ["name"], unique=False)
    op.create_index("ix_finance_accounts_type", "finance_accounts", ["type"], unique=False)

    op.create_table(
        "finance_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_no", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("counterparty_type", sa.String(length=32), nullable=True),
        sa.Column("counterparty_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="normal", nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("voided_by_id", sa.Integer(), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["finance_accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["finance_categories.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_no"),
    )
    op.create_index("ix_finance_records_id", "finance_records", ["id"], unique=False)
    op.create_index("ix_finance_records_record_no", "finance_records", ["record_no"], unique=False)
    op.create_index("ix_finance_records_type", "finance_records", ["type"], unique=False)
    op.create_index("ix_finance_records_status", "finance_records", ["status"], unique=False)
    op.create_index("ix_finance_records_record_date", "finance_records", ["record_date"], unique=False)
    op.create_index("ix_finance_records_category_id", "finance_records", ["category_id"], unique=False)
    op.create_index("ix_finance_records_account_id", "finance_records", ["account_id"], unique=False)

    op.bulk_insert(
        sa.table(
            "finance_categories",
            sa.column("name", sa.String),
            sa.column("type", sa.String),
            sa.column("sort_order", sa.Integer),
            sa.column("is_default", sa.Boolean),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {"name": "其他收入", "type": "income", "sort_order": 0, "is_default": True, "is_active": True},
            {"name": "其他支出", "type": "expense", "sort_order": 0, "is_default": True, "is_active": True},
        ],
    )
    op.bulk_insert(
        sa.table(
            "finance_accounts",
            sa.column("name", sa.String),
            sa.column("type", sa.String),
            sa.column("opening_balance", sa.Numeric),
            sa.column("current_balance", sa.Numeric),
            sa.column("sort_order", sa.Integer),
            sa.column("is_default", sa.Boolean),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {
                "name": "现金",
                "type": "cash",
                "opening_balance": 0,
                "current_balance": 0,
                "sort_order": 0,
                "is_default": True,
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_finance_records_account_id", table_name="finance_records")
    op.drop_index("ix_finance_records_category_id", table_name="finance_records")
    op.drop_index("ix_finance_records_record_date", table_name="finance_records")
    op.drop_index("ix_finance_records_status", table_name="finance_records")
    op.drop_index("ix_finance_records_type", table_name="finance_records")
    op.drop_index("ix_finance_records_record_no", table_name="finance_records")
    op.drop_index("ix_finance_records_id", table_name="finance_records")
    op.drop_table("finance_records")
    op.drop_index("ix_finance_accounts_type", table_name="finance_accounts")
    op.drop_index("ix_finance_accounts_name", table_name="finance_accounts")
    op.drop_index("ix_finance_accounts_id", table_name="finance_accounts")
    op.drop_table("finance_accounts")
    op.drop_index("ix_finance_categories_type", table_name="finance_categories")
    op.drop_index("ix_finance_categories_name", table_name="finance_categories")
    op.drop_index("ix_finance_categories_id", table_name="finance_categories")
    op.drop_table("finance_categories")
