from datetime import date, datetime, time

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.customers.model import Customer
from app.modules.inventory.model import StockMovement, Warehouse
from app.modules.products.model import Product
from app.modules.sales.model import SalesOrder, SalesOrderItem, SalesPayment


class SalesRepository:
    """第 7 阶段新增：销售单数据库读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def next_order_no(self) -> str:
        prefix = f"XS{datetime.now():%Y%m%d}"
        last_no = self.db.scalar(
            select(SalesOrder.order_no)
            .where(SalesOrder.order_no.like(f"{prefix}%"))
            .order_by(SalesOrder.order_no.desc())
            .limit(1)
        )
        seq = int(last_no[-4:]) + 1 if last_no else 1
        return f"{prefix}{seq:04d}"

    def next_payment_no(self) -> str:
        prefix = f"SK{datetime.now():%Y%m%d}"
        last_no = self.db.scalar(
            select(SalesPayment.payment_no)
            .where(SalesPayment.payment_no.like(f"{prefix}%"))
            .order_by(SalesPayment.payment_no.desc())
            .limit(1)
        )
        seq = int(last_no[-4:]) + 1 if last_no else 1
        return f"{prefix}{seq:04d}"

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.db.scalar(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.deleted_at.is_(None),
                Customer.is_active.is_(True),
            )
        )

    def get_product(self, product_id: int) -> Product | None:
        return self.db.scalar(
            select(Product)
            .options(joinedload(Product.unit))
            .where(Product.id == product_id, Product.deleted_at.is_(None), Product.is_active.is_(True))
        )

    def get_warehouse(self, warehouse_id: int) -> Warehouse | None:
        return self.db.scalar(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.deleted_at.is_(None),
                Warehouse.is_active.is_(True),
            )
        )

    def get_default_warehouse(self) -> Warehouse | None:
        return self.db.scalar(
            select(Warehouse).where(
                Warehouse.deleted_at.is_(None),
                Warehouse.is_active.is_(True),
                Warehouse.is_default.is_(True),
            )
        )

    def get_order(self, order_id: int) -> SalesOrder | None:
        return self.db.scalar(
            select(SalesOrder)
            .options(
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.warehouse),
                selectinload(SalesOrder.items).joinedload(SalesOrderItem.product),
                selectinload(SalesOrder.payments).joinedload(SalesPayment.created_by),
            )
            .where(SalesOrder.id == order_id)
        )

    def list_orders(
        self,
        keyword: str | None,
        customer_id: int | None,
        status: str | None,
        delivery_status: str | None,
        payment_status: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[SalesOrder], int]:
        filters = []
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(or_(SalesOrder.order_no.like(like_keyword), Customer.name.like(like_keyword), SalesOrder.remark.like(like_keyword)))
        if customer_id is not None:
            filters.append(SalesOrder.customer_id == customer_id)
        if status:
            filters.append(SalesOrder.status == status)
        if delivery_status:
            filters.append(SalesOrder.delivery_status == delivery_status)
        if payment_status:
            filters.append(SalesOrder.payment_status == payment_status)
        if start_date:
            filters.append(SalesOrder.order_date >= start_date)
        if end_date:
            filters.append(SalesOrder.order_date <= end_date)
        where_clause = and_(*filters) if filters else True
        total = int(
            self.db.scalar(
                select(func.count())
                .select_from(SalesOrder)
                .join(Customer, SalesOrder.customer_id == Customer.id)
                .where(where_clause)
            )
            or 0
        )
        stmt = (
            select(SalesOrder)
            .options(joinedload(SalesOrder.customer), joinedload(SalesOrder.warehouse))
            .join(Customer, SalesOrder.customer_id == Customer.id)
            .where(where_clause)
            .order_by(SalesOrder.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def get_sale_out_movements(self, order_id: int) -> list[StockMovement]:
        stmt = select(StockMovement).where(
            StockMovement.source_type == "sales_order",
            StockMovement.source_id == order_id,
            StockMovement.movement_type == "sale_out",
        )
        return list(self.db.scalars(stmt).all())
