from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.customers.model import Customer
from app.modules.inventory.service import InventoryService
from app.modules.products.model import Product
from app.modules.sales.model import SalesOrder, SalesOrderItem, SalesPayment
from app.modules.sales.repository import SalesRepository
from app.modules.sales.schemas import (
    SalesCancelCreate,
    SalesOrderCreate,
    SalesOrderItemCreate,
    SalesOrderListItem,
    SalesOrderListResponse,
    SalesOrderRead,
    SalesOrderUpdate,
    SalesPaymentCreate,
    SalesPaymentRead,
    SalesShipCreate,
)
from app.modules.users.model import User

QTY = Decimal("0.001")
MONEY = Decimal("0.01")
ZERO_QTY = Decimal("0.000")
ZERO_MONEY = Decimal("0.00")


class SalesService:
    """第 7 阶段新增：销售单业务规则、事务和库存服务调用集中在 service。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SalesRepository(db)
        self.inventory_service = InventoryService(db)

    def list_orders(
        self,
        keyword: str | None,
        customer_id: int | None,
        status_value: str | None,
        delivery_status: str | None,
        payment_status: str | None,
        start_date,
        end_date,
        page: int,
        page_size: int,
    ) -> SalesOrderListResponse:
        orders, total = self.repo.list_orders(
            keyword, customer_id, status_value, delivery_status, payment_status, start_date, end_date, page, page_size
        )
        return SalesOrderListResponse(items=[self._to_list_item(order) for order in orders], total=total, page=page, page_size=page_size)

    def get_order(self, order_id: int) -> SalesOrderRead:
        return self._to_read(self._get_order(order_id))

    def create_order(self, payload: SalesOrderCreate, current_user: User) -> SalesOrderRead:
        try:
            customer = self._get_customer(payload.customer_id)
            warehouse = self._get_warehouse_or_default(payload.warehouse_id)
            order = SalesOrder(
                order_no=self.repo.next_order_no(),
                customer_id=customer.id,
                warehouse_id=warehouse.id,
                order_date=payload.order_date,
                status="draft",
                delivery_status="not_shipped",
                payment_status="unpaid",
                discount_amount=self._money(payload.discount_amount),
                remark=payload.remark,
                created_by_id=current_user.id,
            )
            order.items = [self._build_item(item) for item in payload.items]
            self._recalculate_order(order)
            self.db.add(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def update_order(self, order_id: int, payload: SalesOrderUpdate) -> SalesOrderRead:
        order = self._get_order(order_id)
        if order.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿销售单可以编辑")
        try:
            customer = self._get_customer(payload.customer_id)
            warehouse = self._get_warehouse_or_default(payload.warehouse_id)
            order.customer_id = customer.id
            order.warehouse_id = warehouse.id
            order.order_date = payload.order_date
            order.discount_amount = self._money(payload.discount_amount)
            order.remark = payload.remark
            order.items.clear()
            self.db.flush()
            order.items = [self._build_item(item) for item in payload.items]
            self._recalculate_order(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def confirm_order(self, order_id: int, current_user: User) -> SalesOrderRead:
        order = self._get_order(order_id)
        if order.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿销售单可以确认")
        try:
            order.status = "confirmed"
            order.confirmed_by_id = current_user.id
            order.confirmed_at = datetime.now(timezone.utc)
            order.customer.current_receivable = self._money(order.customer.current_receivable + order.receivable_amount)
            self._recalculate_order(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def ship_order(self, order_id: int, payload: SalesShipCreate, current_user: User) -> SalesOrderRead:
        order = self._get_order(order_id)
        self._ensure_confirmed(order, "只有已确认销售单可以送货")
        item_map = {item.id: item for item in order.items}
        try:
            for ship_item in payload.items:
                item = item_map.get(ship_item.item_id)
                if item is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="销售明细不存在")
                quantity = self._qty(ship_item.quantity)
                remaining = self._qty(item.quantity - item.shipped_quantity)
                if quantity > remaining:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="送货数量不能超过未送数量")
                self.inventory_service.record_sale_out(
                    item.product,
                    order.warehouse,
                    quantity,
                    order.id,
                    payload.remark,
                    current_user,
                )
                item.shipped_quantity = self._qty(item.shipped_quantity + quantity)
            self._recalculate_delivery_status(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def create_payment(self, order_id: int, payload: SalesPaymentCreate, current_user: User) -> SalesOrderRead:
        order = self._get_order(order_id)
        self._ensure_confirmed(order, "只有已确认销售单可以收款")
        amount = self._money(payload.amount)
        if amount > order.unpaid_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="收款金额不能超过未收金额")
        try:
            payment = SalesPayment(
                payment_no=self.repo.next_payment_no(),
                payment_date=payload.payment_date,
                amount=amount,
                method=payload.method,
                remark=payload.remark,
                created_by_id=current_user.id,
            )
            order.payments.append(payment)
            order.customer.current_receivable = self._money(order.customer.current_receivable - amount)
            self.db.flush()
            self._recalculate_order(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def cancel_order(self, order_id: int, payload: SalesCancelCreate, current_user: User) -> SalesOrderRead:
        order = self._get_order(order_id)
        if order.status == "cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="销售单已作废")
        if order.paid_amount > ZERO_MONEY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="第一版暂不支持作废已收款销售单")
        try:
            if order.status == "confirmed":
                for movement in self.repo.get_sale_out_movements(order.id):
                    self.inventory_service.record_cancel_reverse(
                        movement.product,
                        order.warehouse,
                        movement.quantity,
                        movement.unit_cost,
                        order.id,
                        payload.reason,
                        current_user,
                    )
                order.customer.current_receivable = self._money(order.customer.current_receivable - order.unpaid_amount)
            order.status = "cancelled"
            order.cancelled_by_id = current_user.id
            order.cancelled_at = datetime.now(timezone.utc)
            order.cancel_reason = payload.reason
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def _build_item(self, payload: SalesOrderItemCreate) -> SalesOrderItem:
        product = self._get_product(payload.product_id)
        quantity = self._qty(payload.quantity)
        unit_price = self._money(payload.unit_price)
        discount = self._money(payload.discount_amount)
        line_amount = self._money(quantity * unit_price - discount)
        if line_amount < ZERO_MONEY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="明细金额不能小于 0")
        return SalesOrderItem(
            product_id=product.id,
            product_code=product.code,
            product_name=product.name,
            product_barcode=product.barcode,
            product_spec=product.spec,
            product_model=product.model,
            unit_name=product.unit.name if product.unit else None,
            quantity=quantity,
            shipped_quantity=ZERO_QTY,
            unit_price=unit_price,
            discount_amount=discount,
            line_amount=line_amount,
            remark=payload.remark,
        )

    def _recalculate_order(self, order: SalesOrder) -> None:
        order.total_quantity = self._qty(sum((item.quantity for item in order.items), ZERO_QTY))
        order.total_amount = self._money(sum((item.line_amount for item in order.items), ZERO_MONEY))
        order.discount_amount = self._money(order.discount_amount)
        order.receivable_amount = self._money(order.total_amount - order.discount_amount)
        if order.receivable_amount < ZERO_MONEY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="整单应收金额不能小于 0")
        order.paid_amount = self._money(sum((payment.amount for payment in order.payments), ZERO_MONEY))
        order.unpaid_amount = self._money(order.receivable_amount - order.paid_amount)
        self._recalculate_delivery_status(order)
        self._recalculate_payment_status(order)

    def _recalculate_delivery_status(self, order: SalesOrder) -> None:
        if all(item.shipped_quantity == ZERO_QTY for item in order.items):
            order.delivery_status = "not_shipped"
        elif all(item.shipped_quantity >= item.quantity for item in order.items):
            order.delivery_status = "shipped"
        else:
            order.delivery_status = "partial_shipped"

    def _recalculate_payment_status(self, order: SalesOrder) -> None:
        if order.paid_amount == ZERO_MONEY:
            order.payment_status = "unpaid"
        elif order.paid_amount < order.receivable_amount:
            order.payment_status = "partial_paid"
        else:
            order.payment_status = "paid"

    def _get_order(self, order_id: int) -> SalesOrder:
        order = self.repo.get_order(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="销售单不存在")
        return order

    def _get_customer(self, customer_id: int) -> Customer:
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="客户不存在或已禁用")
        return customer

    def _get_product(self, product_id: int) -> Product:
        product = self.repo.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品不存在或已禁用")
        return product

    def _get_warehouse_or_default(self, warehouse_id: int | None):
        warehouse = self.repo.get_warehouse(warehouse_id) if warehouse_id is not None else self.repo.get_default_warehouse()
        if warehouse is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仓库不存在或已停用")
        return warehouse

    def _ensure_confirmed(self, order: SalesOrder, message: str) -> None:
        if order.status != "confirmed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    def _to_list_item(self, order: SalesOrder) -> SalesOrderListItem:
        return SalesOrderListItem(
            id=order.id,
            order_no=order.order_no,
            order_date=order.order_date,
            customer_id=order.customer_id,
            customer_name=order.customer.name,
            status=order.status,
            delivery_status=order.delivery_status,
            payment_status=order.payment_status,
            total_quantity=order.total_quantity,
            receivable_amount=order.receivable_amount,
            paid_amount=order.paid_amount,
            unpaid_amount=order.unpaid_amount,
            created_at=order.created_at,
        )

    def _to_read(self, order: SalesOrder) -> SalesOrderRead:
        base = self._to_list_item(order).model_dump()
        return SalesOrderRead(
            **base,
            warehouse_id=order.warehouse_id,
            warehouse_name=order.warehouse.name,
            total_amount=order.total_amount,
            discount_amount=order.discount_amount,
            remark=order.remark,
            confirmed_at=order.confirmed_at,
            cancelled_at=order.cancelled_at,
            cancel_reason=order.cancel_reason,
            updated_at=order.updated_at,
            items=[
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_code": item.product_code,
                    "product_name": item.product_name,
                    "product_barcode": item.product_barcode,
                    "product_spec": item.product_spec,
                    "product_model": item.product_model,
                    "unit_name": item.unit_name,
                    "quantity": item.quantity,
                    "shipped_quantity": item.shipped_quantity,
                    "unit_price": item.unit_price,
                    "discount_amount": item.discount_amount,
                    "line_amount": item.line_amount,
                    "remark": item.remark,
                }
                for item in order.items
            ],
            payments=[
                SalesPaymentRead(
                    id=payment.id,
                    payment_no=payment.payment_no,
                    payment_date=payment.payment_date,
                    amount=payment.amount,
                    method=payment.method,
                    remark=payment.remark,
                    created_by_id=payment.created_by_id,
                    created_by_name=payment.created_by.display_name if payment.created_by else None,
                    created_at=payment.created_at,
                )
                for payment in order.payments
            ],
        )

    def _qty(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(QTY, rounding=ROUND_HALF_UP)

    def _money(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)
