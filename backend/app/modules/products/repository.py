from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.products.model import Product, ProductCategory, ProductUnit


class ProductRepository:
    """第 5 阶段新增：产品档案数据库读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self) -> list[ProductCategory]:
        stmt = (
            select(ProductCategory)
            .where(ProductCategory.deleted_at.is_(None))
            .order_by(ProductCategory.sort_order.asc(), ProductCategory.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_units(self) -> list[ProductUnit]:
        stmt = (
            select(ProductUnit)
            .where(ProductUnit.deleted_at.is_(None))
            .order_by(ProductUnit.sort_order.asc(), ProductUnit.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: int) -> ProductCategory | None:
        return self.db.scalar(
            select(ProductCategory).where(ProductCategory.id == category_id, ProductCategory.deleted_at.is_(None))
        )

    def get_unit(self, unit_id: int) -> ProductUnit | None:
        return self.db.scalar(select(ProductUnit).where(ProductUnit.id == unit_id, ProductUnit.deleted_at.is_(None)))

    def get_category_by_name(self, name: str) -> ProductCategory | None:
        return self.db.scalar(
            select(ProductCategory).where(ProductCategory.name == name, ProductCategory.deleted_at.is_(None))
        )

    def get_unit_by_name(self, name: str) -> ProductUnit | None:
        return self.db.scalar(select(ProductUnit).where(ProductUnit.name == name, ProductUnit.deleted_at.is_(None)))

    def has_other_category_with_name(self, name: str, category_id: int) -> bool:
        stmt = select(func.count()).select_from(ProductCategory).where(
            ProductCategory.name == name,
            ProductCategory.id != category_id,
            ProductCategory.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def has_other_unit_with_name(self, name: str, unit_id: int) -> bool:
        stmt = select(func.count()).select_from(ProductUnit).where(
            ProductUnit.name == name,
            ProductUnit.id != unit_id,
            ProductUnit.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def count_products_by_category(self, category_id: int) -> int:
        stmt = select(func.count()).select_from(Product).where(
            Product.category_id == category_id,
            Product.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)

    def count_products_by_unit(self, unit_id: int) -> int:
        stmt = select(func.count()).select_from(Product).where(Product.unit_id == unit_id, Product.deleted_at.is_(None))
        return int(self.db.scalar(stmt) or 0)

    def count_active_categories(self, exclude_category_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(ProductCategory).where(ProductCategory.deleted_at.is_(None))
        if exclude_category_id is not None:
            stmt = stmt.where(ProductCategory.id != exclude_category_id)
        return int(self.db.scalar(stmt) or 0)

    def count_active_units(self, exclude_unit_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(ProductUnit).where(ProductUnit.deleted_at.is_(None))
        if exclude_unit_id is not None:
            stmt = stmt.where(ProductUnit.id != exclude_unit_id)
        return int(self.db.scalar(stmt) or 0)

    def get_product(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.unit))
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )
        return self.db.scalar(stmt)

    def get_product_by_name(self, name: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.name == name, Product.deleted_at.is_(None)))

    def get_product_by_code(self, code: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.code == code, Product.deleted_at.is_(None)))

    def get_product_by_barcode(self, barcode: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.barcode == barcode, Product.deleted_at.is_(None)))

    def has_other_product_with_name(self, name: str, product_id: int) -> bool:
        stmt = select(func.count()).select_from(Product).where(
            Product.name == name,
            Product.id != product_id,
            Product.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def has_other_product_with_code(self, code: str, product_id: int) -> bool:
        stmt = select(func.count()).select_from(Product).where(
            Product.code == code,
            Product.id != product_id,
            Product.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def has_other_product_with_barcode(self, barcode: str, product_id: int) -> bool:
        stmt = select(func.count()).select_from(Product).where(
            Product.barcode == barcode,
            Product.id != product_id,
            Product.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def list_products(
        self,
        keyword: str | None,
        category_id: int | None,
        unit_id: int | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        filters = [Product.deleted_at.is_(None)]
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    Product.name.like(like_keyword),
                    Product.code.like(like_keyword),
                    Product.barcode.like(like_keyword),
                    Product.spec.like(like_keyword),
                    Product.model.like(like_keyword),
                    Product.brand.like(like_keyword),
                )
            )
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if unit_id is not None:
            filters.append(Product.unit_id == unit_id)
        if is_active is not None:
            filters.append(Product.is_active.is_(is_active))

        count_stmt = select(func.count()).select_from(Product).where(and_(*filters))
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.unit))
            .where(and_(*filters))
            .order_by(Product.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def soft_delete_category(self, category: ProductCategory) -> ProductCategory:
        category.deleted_at = datetime.now(timezone.utc)
        return category

    def soft_delete_unit(self, unit: ProductUnit) -> ProductUnit:
        unit.deleted_at = datetime.now(timezone.utc)
        return unit

    def soft_delete_product(self, product: Product) -> Product:
        product.deleted_at = datetime.now(timezone.utc)
        product.is_active = False
        return product
