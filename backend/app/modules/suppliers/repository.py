from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.suppliers.model import Supplier, SupplierCategory


class SupplierRepository:
    """第 4 阶段新增：供应商模块数据库读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self) -> list[SupplierCategory]:
        stmt = (
            select(SupplierCategory)
            .where(SupplierCategory.deleted_at.is_(None))
            .order_by(SupplierCategory.sort_order.asc(), SupplierCategory.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: int, include_deleted: bool = False) -> SupplierCategory | None:
        stmt = select(SupplierCategory).where(SupplierCategory.id == category_id)
        if not include_deleted:
            stmt = stmt.where(SupplierCategory.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_category_by_name(self, name: str) -> SupplierCategory | None:
        return self.db.scalar(
            select(SupplierCategory).where(
                SupplierCategory.name == name,
                SupplierCategory.deleted_at.is_(None),
            )
        )

    def has_other_category_with_name(self, name: str, category_id: int) -> bool:
        stmt = select(func.count()).select_from(SupplierCategory).where(
            SupplierCategory.name == name,
            SupplierCategory.id != category_id,
            SupplierCategory.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def count_suppliers_by_category(self, category_id: int) -> int:
        stmt = select(func.count()).select_from(Supplier).where(
            Supplier.category_id == category_id,
            Supplier.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)

    def count_active_categories(self, exclude_category_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(SupplierCategory).where(SupplierCategory.deleted_at.is_(None))
        if exclude_category_id is not None:
            stmt = stmt.where(SupplierCategory.id != exclude_category_id)
        return int(self.db.scalar(stmt) or 0)

    def get_supplier(self, supplier_id: int, include_deleted: bool = False) -> Supplier | None:
        stmt = select(Supplier).options(joinedload(Supplier.category)).where(Supplier.id == supplier_id)
        if not include_deleted:
            stmt = stmt.where(Supplier.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_supplier_by_name(self, name: str) -> Supplier | None:
        return self.db.scalar(select(Supplier).where(Supplier.name == name, Supplier.deleted_at.is_(None)))

    def has_other_supplier_with_name(self, name: str, supplier_id: int) -> bool:
        stmt = select(func.count()).select_from(Supplier).where(
            Supplier.name == name,
            Supplier.id != supplier_id,
            Supplier.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def list_suppliers(
        self,
        keyword: str | None,
        category_id: int | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Supplier], int]:
        filters = [Supplier.deleted_at.is_(None)]
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    Supplier.name.like(like_keyword),
                    Supplier.code.like(like_keyword),
                    Supplier.contact_name.like(like_keyword),
                    Supplier.phone.like(like_keyword),
                    Supplier.address.like(like_keyword),
                )
            )
        if category_id is not None:
            filters.append(Supplier.category_id == category_id)
        if is_active is not None:
            filters.append(Supplier.is_active.is_(is_active))

        count_stmt = select(func.count()).select_from(Supplier).where(and_(*filters))
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = (
            select(Supplier)
            .options(joinedload(Supplier.category))
            .where(and_(*filters))
            .order_by(Supplier.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def soft_delete_category(self, category: SupplierCategory) -> SupplierCategory:
        category.deleted_at = datetime.now(timezone.utc)
        return category

    def soft_delete_supplier(self, supplier: Supplier) -> Supplier:
        supplier.deleted_at = datetime.now(timezone.utc)
        supplier.is_active = False
        return supplier

