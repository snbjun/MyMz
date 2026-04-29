"""create product categories units and products

Revision ID: 20260429_0004
Revises: 20260429_0003
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260429_0004"
down_revision: str | None = "20260429_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_categories_id", "product_categories", ["id"], unique=False)
    op.create_index("ix_product_categories_deleted_at", "product_categories", ["deleted_at"], unique=False)
    op.create_index(
        "uq_product_categories_name_active",
        "product_categories",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "product_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_units_id", "product_units", ["id"], unique=False)
    op.create_index("ix_product_units_deleted_at", "product_units", ["deleted_at"], unique=False)
    op.create_index(
        "uq_product_units_name_active",
        "product_units",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("barcode", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("spec", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("brand", sa.String(length=128), nullable=True),
        sa.Column("origin", sa.String(length=128), nullable=True),
        sa.Column("sale_price", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("purchase_price", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("wholesale_price", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("stock_warning_qty", sa.Numeric(18, 3), server_default="0", nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["product_units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_code", "products", ["code"], unique=False)
    op.create_index("ix_products_barcode", "products", ["barcode"], unique=False)
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_products_unit_id", "products", ["unit_id"], unique=False)
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"], unique=False)
    op.create_index(
        "uq_products_name_active",
        "products",
        ["name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_products_code_active",
        "products",
        ["code"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND code IS NOT NULL AND code != ''"),
    )
    op.create_index(
        "uq_products_barcode_active",
        "products",
        ["barcode"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND barcode IS NOT NULL AND barcode != ''"),
    )

    op.execute(sa.text("INSERT INTO product_categories (name, sort_order, is_default) VALUES ('默认分类', 0, 1)"))
    op.execute(sa.text("INSERT INTO product_units (name, sort_order, is_default) VALUES ('个', 0, 1)"))


def downgrade() -> None:
    op.drop_index("uq_products_barcode_active", table_name="products")
    op.drop_index("uq_products_code_active", table_name="products")
    op.drop_index("uq_products_name_active", table_name="products")
    op.drop_index("ix_products_deleted_at", table_name="products")
    op.drop_index("ix_products_unit_id", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_index("ix_products_code", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_table("products")
    op.drop_index("uq_product_units_name_active", table_name="product_units")
    op.drop_index("ix_product_units_deleted_at", table_name="product_units")
    op.drop_index("ix_product_units_id", table_name="product_units")
    op.drop_table("product_units")
    op.drop_index("uq_product_categories_name_active", table_name="product_categories")
    op.drop_index("ix_product_categories_deleted_at", table_name="product_categories")
    op.drop_index("ix_product_categories_id", table_name="product_categories")
    op.drop_table("product_categories")
