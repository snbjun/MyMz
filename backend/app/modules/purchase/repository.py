from datetime import date, datetime, time

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.suppliers.model import Supplier
from app.modules.inventory.model import StockMovement, Warehouse
from app.modules.products.model import Product
from app.modules.purchase.model import PurchaseOrder, PurchaseOrderItem, PurchasePayment


class PurchaseRepository:
    """第 8 阶段新增：采购单数据库读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def next_order_no(self) -> str:
        prefix = f"CG{datetime.now():%Y%m%d}"
        last_no = self.db.scalar(
            select(PurchaseOrder.order_no)
            .where(PurchaseOrder.order_no.like(f"{prefix}%"))
            .order_by(PurchaseOrder.order_no.desc())
            .limit(1)
        )
        seq = int(last_no[-4:]) + 1 if last_no else 1
        return f"{prefix}{seq:04d}"

    def next_payment_no(self) -> str:
        prefix = f"FK{datetime.now():%Y%m%d}"
        last_no = self.db.scalar(
            select(PurchasePayment.payment_no)
            .where(PurchasePayment.payment_no.like(f"{prefix}%"))
            .order_by(PurchasePayment.payment_no.desc())
            .limit(1)
        )
        seq = int(last_no[-4:]) + 1 if last_no else 1
        return f"{prefix}{seq:04d}"

    def get_supplier(self, supplier_id: int) -> Supplier | None:
        return self.db.scalar(
            select(Supplier).where(
                Supplier.id == supplier_id,
                Supplier.deleted_at.is_(None),
                Supplier.is_active.is_(True),
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

    def get_order(self, order_id: int) -> PurchaseOrder | None:
        return self.db.scalar(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.warehouse),
                selectinload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
                selectinload(PurchaseOrder.payments).joinedload(PurchasePayment.created_by),
            )
            .where(PurchaseOrder.id == order_id)
        )

    def list_orders(
        self,
        keyword: str | None,
        supplier_id: int | None,
        status: str | None,
        receive_status: str | None,
        payment_status: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[PurchaseOrder], int]:
        filters = []
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(or_(PurchaseOrder.order_no.like(like_keyword), Supplier.name.like(like_keyword), PurchaseOrder.remark.like(like_keyword)))
        if supplier_id is not None:
            filters.append(PurchaseOrder.supplier_id == supplier_id)
        if status:
            filters.append(PurchaseOrder.status == status)
        if receive_status:
            filters.append(PurchaseOrder.receive_status == receive_status)
        if payment_status:
            filters.append(PurchaseOrder.payment_status == payment_status)
        if start_date:
            filters.append(PurchaseOrder.order_date >= start_date)
        if end_date:
            filters.append(PurchaseOrder.order_date <= end_date)
        where_clause = and_(*filters) if filters else True
        total = int(
            self.db.scalar(
                select(func.count())
                .select_from(PurchaseOrder)
                .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)
                .where(where_clause)
            )
            or 0
        )
        stmt = (
            select(PurchaseOrder)
            .options(joinedload(PurchaseOrder.supplier), joinedload(PurchaseOrder.warehouse))
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)
            .where(where_clause)
            .order_by(PurchaseOrder.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def get_purchase_in_movements(self, order_id: int) -> list[StockMovement]:
        stmt = select(StockMovement).where(
            StockMovement.source_type == "purchase_order",
            StockMovement.source_id == order_id,
            StockMovement.movement_type == "purchase_in",
        )
        return list(self.db.scalars(stmt).all())
