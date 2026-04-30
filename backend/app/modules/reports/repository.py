from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import and_, case, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.modules.customers.model import Customer
from app.modules.finance.model import FinanceAccount, FinanceCategory, FinanceRecord
from app.modules.inventory.model import Inventory, StockMovement
from app.modules.products.model import Product
from app.modules.purchase.model import PurchaseOrder, PurchaseOrderItem
from app.modules.sales.model import SalesOrder, SalesOrderItem
from app.modules.suppliers.model import Supplier


class ReportRepository:
    """第 10 阶段新增：报表只读聚合查询集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def sales_summary(self, start_date: date, end_date: date) -> dict:
        row = self.db.execute(
            select(
                func.count(SalesOrder.id),
                func.coalesce(func.sum(SalesOrder.total_quantity), 0),
                func.coalesce(func.sum(SalesOrder.receivable_amount), 0),
                func.coalesce(func.sum(SalesOrder.paid_amount), 0),
                func.coalesce(func.sum(SalesOrder.unpaid_amount), 0),
            ).where(self._sales_filters(start_date, end_date))
        ).one()
        return {
            "order_count": int(row[0] or 0),
            "total_quantity": self._decimal(row[1]),
            "receivable_amount": self._decimal(row[2]),
            "paid_amount": self._decimal(row[3]),
            "unpaid_amount": self._decimal(row[4]),
        }

    def sales_by_customer(self, start_date: date, end_date: date, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = self._sales_filters(start_date, end_date)
        grouped = (
            select(SalesOrder.customer_id)
            .where(filters)
            .group_by(SalesOrder.customer_id)
            .subquery()
        )
        total = int(self.db.scalar(select(func.count()).select_from(grouped)) or 0)
        stmt = (
            select(
                SalesOrder.customer_id,
                Customer.name,
                func.count(SalesOrder.id),
                func.coalesce(func.sum(SalesOrder.receivable_amount), 0),
                func.coalesce(func.sum(SalesOrder.paid_amount), 0),
                func.coalesce(func.sum(SalesOrder.unpaid_amount), 0),
            )
            .join(Customer, SalesOrder.customer_id == Customer.id)
            .where(filters)
            .group_by(SalesOrder.customer_id, Customer.name)
            .order_by(func.sum(SalesOrder.receivable_amount).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {
                "customer_id": row[0],
                "customer_name": row[1],
                "order_count": int(row[2] or 0),
                "sales_amount": self._decimal(row[3]),
                "paid_amount": self._decimal(row[4]),
                "unpaid_amount": self._decimal(row[5]),
            }
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def sales_by_product(self, start_date: date, end_date: date, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = self._sales_filters(start_date, end_date)
        grouped = (
            select(SalesOrderItem.product_id, SalesOrderItem.product_code, SalesOrderItem.product_name)
            .join(SalesOrder, SalesOrderItem.sales_order_id == SalesOrder.id)
            .where(filters)
            .group_by(SalesOrderItem.product_id, SalesOrderItem.product_code, SalesOrderItem.product_name)
            .subquery()
        )
        total = int(self.db.scalar(select(func.count()).select_from(grouped)) or 0)
        stmt = (
            select(
                SalesOrderItem.product_id,
                SalesOrderItem.product_code,
                SalesOrderItem.product_name,
                func.coalesce(func.sum(SalesOrderItem.quantity), 0),
                func.coalesce(func.sum(SalesOrderItem.line_amount), 0),
            )
            .join(SalesOrder, SalesOrderItem.sales_order_id == SalesOrder.id)
            .where(filters)
            .group_by(SalesOrderItem.product_id, SalesOrderItem.product_code, SalesOrderItem.product_name)
            .order_by(func.sum(SalesOrderItem.line_amount).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {
                "product_id": row[0],
                "product_code": row[1],
                "product_name": row[2],
                "quantity": self._decimal(row[3]),
                "sales_amount": self._decimal(row[4]),
            }
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def purchase_summary(self, start_date: date, end_date: date) -> dict:
        row = self.db.execute(
            select(
                func.count(PurchaseOrder.id),
                func.coalesce(func.sum(PurchaseOrder.total_quantity), 0),
                func.coalesce(func.sum(PurchaseOrder.payable_amount), 0),
                func.coalesce(func.sum(PurchaseOrder.paid_amount), 0),
                func.coalesce(func.sum(PurchaseOrder.unpaid_amount), 0),
            ).where(self._purchase_filters(start_date, end_date))
        ).one()
        return {
            "order_count": int(row[0] or 0),
            "total_quantity": self._decimal(row[1]),
            "payable_amount": self._decimal(row[2]),
            "paid_amount": self._decimal(row[3]),
            "unpaid_amount": self._decimal(row[4]),
        }

    def purchase_by_supplier(self, start_date: date, end_date: date, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = self._purchase_filters(start_date, end_date)
        grouped = select(PurchaseOrder.supplier_id).where(filters).group_by(PurchaseOrder.supplier_id).subquery()
        total = int(self.db.scalar(select(func.count()).select_from(grouped)) or 0)
        stmt = (
            select(
                PurchaseOrder.supplier_id,
                Supplier.name,
                func.count(PurchaseOrder.id),
                func.coalesce(func.sum(PurchaseOrder.payable_amount), 0),
                func.coalesce(func.sum(PurchaseOrder.paid_amount), 0),
                func.coalesce(func.sum(PurchaseOrder.unpaid_amount), 0),
            )
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)
            .where(filters)
            .group_by(PurchaseOrder.supplier_id, Supplier.name)
            .order_by(func.sum(PurchaseOrder.payable_amount).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {
                "supplier_id": row[0],
                "supplier_name": row[1],
                "order_count": int(row[2] or 0),
                "purchase_amount": self._decimal(row[3]),
                "paid_amount": self._decimal(row[4]),
                "unpaid_amount": self._decimal(row[5]),
            }
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def purchase_by_product(self, start_date: date, end_date: date, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = self._purchase_filters(start_date, end_date)
        grouped = (
            select(PurchaseOrderItem.product_id, PurchaseOrderItem.product_code, PurchaseOrderItem.product_name)
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(filters)
            .group_by(PurchaseOrderItem.product_id, PurchaseOrderItem.product_code, PurchaseOrderItem.product_name)
            .subquery()
        )
        total = int(self.db.scalar(select(func.count()).select_from(grouped)) or 0)
        stmt = (
            select(
                PurchaseOrderItem.product_id,
                PurchaseOrderItem.product_code,
                PurchaseOrderItem.product_name,
                func.coalesce(func.sum(PurchaseOrderItem.quantity), 0),
                func.coalesce(func.sum(PurchaseOrderItem.line_amount), 0),
            )
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(filters)
            .group_by(PurchaseOrderItem.product_id, PurchaseOrderItem.product_code, PurchaseOrderItem.product_name)
            .order_by(func.sum(PurchaseOrderItem.line_amount).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {
                "product_id": row[0],
                "product_code": row[1],
                "product_name": row[2],
                "quantity": self._decimal(row[3]),
                "purchase_amount": self._decimal(row[4]),
            }
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def receivable_summary(self) -> dict:
        row = self.db.execute(
            select(func.count(Customer.id), func.coalesce(func.sum(Customer.current_receivable), 0)).where(Customer.deleted_at.is_(None))
        ).one()
        return {"customer_count": int(row[0] or 0), "total_receivable": self._decimal(row[1])}

    def receivables(self, keyword: str | None, include_zero: bool, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = [Customer.deleted_at.is_(None)]
        if not include_zero:
            filters.append(Customer.current_receivable != 0)
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(or_(Customer.name.like(like_keyword), Customer.code.like(like_keyword), Customer.phone.like(like_keyword)))
        where_clause = and_(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(Customer).where(where_clause)) or 0)
        stmt = (
            select(Customer.id, Customer.code, Customer.name, Customer.phone, Customer.current_receivable)
            .where(where_clause)
            .order_by(Customer.current_receivable.desc(), Customer.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {
                "customer_id": row[0],
                "customer_code": row[1],
                "customer_name": row[2],
                "phone": row[3],
                "current_receivable": self._decimal(row[4]),
            }
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def payable_summary(self) -> dict:
        row = self.db.execute(
            select(func.count(Supplier.id), func.coalesce(func.sum(Supplier.current_payable), 0)).where(Supplier.deleted_at.is_(None))
        ).one()
        return {"supplier_count": int(row[0] or 0), "total_payable": self._decimal(row[1])}

    def payables(self, keyword: str | None, include_zero: bool, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = [Supplier.deleted_at.is_(None)]
        if not include_zero:
            filters.append(Supplier.current_payable != 0)
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(or_(Supplier.name.like(like_keyword), Supplier.code.like(like_keyword), Supplier.phone.like(like_keyword)))
        where_clause = and_(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(Supplier).where(where_clause)) or 0)
        stmt = (
            select(Supplier.id, Supplier.code, Supplier.name, Supplier.phone, Supplier.current_payable)
            .where(where_clause)
            .order_by(Supplier.current_payable.desc(), Supplier.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {
                "supplier_id": row[0],
                "supplier_code": row[1],
                "supplier_name": row[2],
                "phone": row[3],
                "current_payable": self._decimal(row[4]),
            }
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def inventory_summary(self) -> dict:
        inv_by_product = (
            select(
                Inventory.product_id.label("product_id"),
                func.coalesce(func.sum(Inventory.quantity_on_hand), 0).label("quantity"),
                func.coalesce(func.sum(Inventory.total_cost), 0).label("total_cost"),
            )
            .group_by(Inventory.product_id)
            .subquery()
        )
        row = self.db.execute(
            select(
                func.count(Product.id),
                func.coalesce(func.sum(inv_by_product.c.quantity), 0),
                func.coalesce(func.sum(inv_by_product.c.total_cost), 0),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    Product.is_active.is_(True),
                                    Product.stock_warning_qty > 0,
                                    func.coalesce(inv_by_product.c.quantity, 0) <= Product.stock_warning_qty,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .select_from(Product)
            .outerjoin(inv_by_product, Product.id == inv_by_product.c.product_id)
            .where(Product.deleted_at.is_(None))
        ).one()
        return {
            "product_count": int(row[0] or 0),
            "total_quantity": self._decimal(row[1]),
            "total_cost": self._decimal(row[2]),
            "low_stock_count": int(row[3] or 0),
        }

    def inventory_movement_summary(self, start_date: date, end_date: date) -> dict:
        filters = self._movement_filters(start_date, end_date)
        total_row = self.db.execute(
            select(
                func.coalesce(func.sum(case((StockMovement.direction == "in", StockMovement.quantity), else_=0)), 0),
                func.coalesce(func.sum(case((StockMovement.direction == "out", StockMovement.quantity), else_=0)), 0),
                func.coalesce(func.sum(case((StockMovement.direction == "in", StockMovement.amount), else_=0)), 0),
                func.coalesce(func.sum(case((StockMovement.direction == "out", StockMovement.amount), else_=0)), 0),
            ).where(filters)
        ).one()
        stmt = (
            select(
                StockMovement.movement_type,
                StockMovement.direction,
                func.coalesce(func.sum(StockMovement.quantity), 0),
                func.coalesce(func.sum(StockMovement.amount), 0),
            )
            .where(filters)
            .group_by(StockMovement.movement_type, StockMovement.direction)
            .order_by(StockMovement.movement_type.asc())
        )
        return {
            "in_quantity": self._decimal(total_row[0]),
            "out_quantity": self._decimal(total_row[1]),
            "in_amount": self._decimal(total_row[2]),
            "out_amount": self._decimal(total_row[3]),
            "items": [
                {
                    "movement_type": row[0],
                    "direction": row[1],
                    "quantity": self._decimal(row[2]),
                    "amount": self._decimal(row[3]),
                }
                for row in self.db.execute(stmt).all()
            ],
        }

    def finance_summary(self, start_date: date, end_date: date) -> dict:
        accounts = self.db.execute(
            select(
                FinanceAccount.id,
                FinanceAccount.name,
                FinanceAccount.type,
                FinanceAccount.opening_balance,
                FinanceAccount.current_balance,
            )
            .where(FinanceAccount.deleted_at.is_(None))
            .order_by(FinanceAccount.sort_order.asc(), FinanceAccount.id.asc())
        ).all()
        finance_row = self.db.execute(
            select(
                func.coalesce(func.sum(case((FinanceRecord.type == "income", FinanceRecord.amount), else_=0)), 0),
                func.coalesce(func.sum(case((FinanceRecord.type == "expense", FinanceRecord.amount), else_=0)), 0),
            ).where(self._finance_filters(start_date, end_date))
        ).one()
        income_amount = self._decimal(finance_row[0])
        expense_amount = self._decimal(finance_row[1])
        return {
            "account_count": len(accounts),
            "balance_total": self._decimal(sum((self._decimal(row[4]) for row in accounts), Decimal("0.00"))),
            "income_amount": income_amount,
            "expense_amount": expense_amount,
            "net_amount": income_amount - expense_amount,
            "accounts": [
                {
                    "account_id": row[0],
                    "account_name": row[1],
                    "account_type": row[2],
                    "opening_balance": self._decimal(row[3]),
                    "current_balance": self._decimal(row[4]),
                }
                for row in accounts
            ],
        }

    def finance_by_category(self, start_date: date, end_date: date, page: int, page_size: int) -> tuple[list[dict], int]:
        filters = self._finance_filters(start_date, end_date)
        grouped = (
            select(FinanceRecord.category_id, FinanceRecord.type)
            .where(filters)
            .group_by(FinanceRecord.category_id, FinanceRecord.type)
            .subquery()
        )
        total = int(self.db.scalar(select(func.count()).select_from(grouped)) or 0)
        stmt = (
            select(FinanceRecord.category_id, FinanceCategory.name, FinanceRecord.type, func.coalesce(func.sum(FinanceRecord.amount), 0))
            .join(FinanceCategory, FinanceRecord.category_id == FinanceCategory.id)
            .where(filters)
            .group_by(FinanceRecord.category_id, FinanceCategory.name, FinanceRecord.type)
            .order_by(FinanceRecord.type.asc(), func.sum(FinanceRecord.amount).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [
            {"category_id": row[0], "category_name": row[1], "type": row[2], "amount": self._decimal(row[3])}
            for row in self.db.execute(stmt).all()
        ]
        return items, total

    def _sales_filters(self, start_date: date, end_date: date):
        return and_(SalesOrder.status == "confirmed", SalesOrder.order_date >= start_date, SalesOrder.order_date <= end_date)

    def _purchase_filters(self, start_date: date, end_date: date):
        return and_(PurchaseOrder.status == "confirmed", PurchaseOrder.order_date >= start_date, PurchaseOrder.order_date <= end_date)

    def _finance_filters(self, start_date: date, end_date: date):
        return and_(FinanceRecord.status == "normal", FinanceRecord.record_date >= start_date, FinanceRecord.record_date <= end_date)

    def _movement_filters(self, start_date: date, end_date: date):
        return and_(
            StockMovement.created_at >= datetime.combine(start_date, time.min),
            StockMovement.created_at <= datetime.combine(end_date, time.max),
        )

    def _decimal(self, value) -> Decimal:
        return Decimal(str(value or 0))
