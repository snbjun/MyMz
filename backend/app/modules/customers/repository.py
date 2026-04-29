from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.customers.model import Customer, CustomerCategory


class CustomerRepository:
    """第 3 阶段新增：客户模块数据库读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self) -> list[CustomerCategory]:
        stmt = (
            select(CustomerCategory)
            .where(CustomerCategory.deleted_at.is_(None))
            .order_by(CustomerCategory.sort_order.asc(), CustomerCategory.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: int, include_deleted: bool = False) -> CustomerCategory | None:
        stmt = select(CustomerCategory).where(CustomerCategory.id == category_id)
        if not include_deleted:
            stmt = stmt.where(CustomerCategory.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_category_by_name(self, name: str) -> CustomerCategory | None:
        return self.db.scalar(
            select(CustomerCategory).where(
                CustomerCategory.name == name,
                CustomerCategory.deleted_at.is_(None),
            )
        )

    def has_other_category_with_name(self, name: str, category_id: int) -> bool:
        stmt = select(func.count()).select_from(CustomerCategory).where(
            CustomerCategory.name == name,
            CustomerCategory.id != category_id,
            CustomerCategory.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def count_customers_by_category(self, category_id: int) -> int:
        stmt = select(func.count()).select_from(Customer).where(
            Customer.category_id == category_id,
            Customer.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)

    def count_active_categories(self, exclude_category_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(CustomerCategory).where(CustomerCategory.deleted_at.is_(None))
        if exclude_category_id is not None:
            stmt = stmt.where(CustomerCategory.id != exclude_category_id)
        return int(self.db.scalar(stmt) or 0)

    def get_customer(self, customer_id: int, include_deleted: bool = False) -> Customer | None:
        stmt = select(Customer).options(joinedload(Customer.category)).where(Customer.id == customer_id)
        if not include_deleted:
            stmt = stmt.where(Customer.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_customer_by_name(self, name: str) -> Customer | None:
        return self.db.scalar(select(Customer).where(Customer.name == name, Customer.deleted_at.is_(None)))

    def has_other_customer_with_name(self, name: str, customer_id: int) -> bool:
        stmt = select(func.count()).select_from(Customer).where(
            Customer.name == name,
            Customer.id != customer_id,
            Customer.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0) > 0

    def list_customers(
        self,
        keyword: str | None,
        category_id: int | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Customer], int]:
        filters = [Customer.deleted_at.is_(None)]
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    Customer.name.like(like_keyword),
                    Customer.code.like(like_keyword),
                    Customer.contact_name.like(like_keyword),
                    Customer.phone.like(like_keyword),
                    Customer.address.like(like_keyword),
                )
            )
        if category_id is not None:
            filters.append(Customer.category_id == category_id)
        if is_active is not None:
            filters.append(Customer.is_active.is_(is_active))

        count_stmt = select(func.count()).select_from(Customer).where(and_(*filters))
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = (
            select(Customer)
            .options(joinedload(Customer.category))
            .where(and_(*filters))
            .order_by(Customer.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def soft_delete_category(self, category: CustomerCategory) -> CustomerCategory:
        category.deleted_at = datetime.now(timezone.utc)
        return category

    def soft_delete_customer(self, customer: Customer) -> Customer:
        customer.deleted_at = datetime.now(timezone.utc)
        customer.is_active = False
        return customer
