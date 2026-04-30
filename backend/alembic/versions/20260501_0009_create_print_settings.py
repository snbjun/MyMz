"""create print settings

Revision ID: 20260501_0009
Revises: 20260430_0008
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0009"
down_revision: str | None = "20260430_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "print_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("template_name", sa.String(length=64), server_default="标准模板", nullable=False),
        sa.Column("paper_size", sa.String(length=16), server_default="A4", nullable=False),
        sa.Column("show_company_name", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("company_name", sa.String(length=128), nullable=True),
        sa.Column("show_contact", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("contact_text", sa.String(length=255), nullable=True),
        sa.Column("show_amount", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("show_unit_price", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("show_discount", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("show_remark", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("show_signature", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("footer_text", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_type"),
    )
    op.create_index("ix_print_settings_id", "print_settings", ["id"], unique=False)
    op.create_index("ix_print_settings_doc_type", "print_settings", ["doc_type"], unique=False)
    op.bulk_insert(
        sa.table(
            "print_settings",
            sa.column("doc_type", sa.String),
            sa.column("template_name", sa.String),
            sa.column("paper_size", sa.String),
            sa.column("show_company_name", sa.Boolean),
            sa.column("show_contact", sa.Boolean),
            sa.column("show_amount", sa.Boolean),
            sa.column("show_unit_price", sa.Boolean),
            sa.column("show_discount", sa.Boolean),
            sa.column("show_remark", sa.Boolean),
            sa.column("show_signature", sa.Boolean),
            sa.column("is_default", sa.Boolean),
        ),
        [
            {
                "doc_type": "sales_order",
                "template_name": "标准模板",
                "paper_size": "A4",
                "show_company_name": True,
                "show_contact": False,
                "show_amount": True,
                "show_unit_price": True,
                "show_discount": True,
                "show_remark": True,
                "show_signature": True,
                "is_default": True,
            },
            {
                "doc_type": "purchase_order",
                "template_name": "标准模板",
                "paper_size": "A4",
                "show_company_name": True,
                "show_contact": False,
                "show_amount": True,
                "show_unit_price": True,
                "show_discount": True,
                "show_remark": True,
                "show_signature": True,
                "is_default": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_print_settings_doc_type", table_name="print_settings")
    op.drop_index("ix_print_settings_id", table_name="print_settings")
    op.drop_table("print_settings")
