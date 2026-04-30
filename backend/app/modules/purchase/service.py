from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.suppliers.model import Supplier
from app.modules.inventory.service import InventoryService
from app.modules.products.model import Product
from app.modules.purchase.model import PurchaseOrder, PurchaseOrderItem, PurchasePayment
from app.modules.purchase.repository import PurchaseRepository
from app.modules.purchase.schemas import (
    PurchaseCancelCreate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderListItem,
    PurchaseOrderListResponse,
    PurchaseOrderRead,
    PurchaseOrderUpdate,
    PurchasePaymentCreate,
    PurchasePaymentRead,
    PurchaseReceiveCreate,
)
from app.modules.users.model import User

QTY = Decimal("0.001")
MONEY = Decimal("0.01")
ZERO_QTY = Decimal("0.000")
ZERO_MONEY = Decimal("0.00")


class PurchaseService:
    """第 8 阶段新增：采购单业务规则、事务和库存服务调用集中在 service。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PurchaseRepository(db)
        self.inventory_service = InventoryService(db)

    def list_orders(
        self,
        keyword: str | None,
        supplier_id: int | None,
        status_value: str | None,
        receive_status: str | None,
        payment_status: str | None,
        start_date,
        end_date,
        page: int,
        page_size: int,
    ) -> PurchaseOrderListResponse:
        orders, total = self.repo.list_orders(
            keyword, supplier_id, status_value, receive_status, payment_status, start_date, end_date, page, page_size
        )
        return PurchaseOrderListResponse(items=[self._to_list_item(order) for order in orders], total=total, page=page, page_size=page_size)

    def get_order(self, order_id: int) -> PurchaseOrderRead:
        return self._to_read(self._get_order(order_id))

    def create_order(self, payload: PurchaseOrderCreate, current_user: User) -> PurchaseOrderRead:
        try:
            supplier = self._get_supplier(payload.supplier_id)
            warehouse = self._get_warehouse_or_default(payload.warehouse_id)
            order = PurchaseOrder(
                order_no=self.repo.next_order_no(),
                supplier_id=supplier.id,
                warehouse_id=warehouse.id,
                order_date=payload.order_date,
                status="draft",
                receive_status="not_received",
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

    def update_order(self, order_id: int, payload: PurchaseOrderUpdate) -> PurchaseOrderRead:
        order = self._get_order(order_id)
        if order.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿采购单可以编辑")
        try:
            supplier = self._get_supplier(payload.supplier_id)
            warehouse = self._get_warehouse_or_default(payload.warehouse_id)
            order.supplier_id = supplier.id
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

    def confirm_order(self, order_id: int, current_user: User) -> PurchaseOrderRead:
        order = self._get_order(order_id)
        if order.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿采购单可以确认")
        try:
            order.status = "confirmed"
            order.confirmed_by_id = current_user.id
            order.confirmed_at = datetime.now(timezone.utc)
            order.supplier.current_payable = self._money(order.supplier.current_payable + order.payable_amount)
            self._recalculate_order(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def receive_order(self, order_id: int, payload: PurchaseReceiveCreate, current_user: User) -> PurchaseOrderRead:
        order = self._get_order(order_id)
        self._ensure_confirmed(order, "只有已确认采购单可以收货")
        item_map = {item.id: item for item in order.items}
        try:
            for receive_item in payload.items:
                item = item_map.get(receive_item.item_id)
                if item is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="采购明细不存在")
                quantity = self._qty(receive_item.quantity)
                remaining = self._qty(item.quantity - item.received_quantity)
                if quantity > remaining:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="收货数量不能超过未收数量")
                self.inventory_service.record_purchase_in(
                    item.product,
                    order.warehouse,
                    quantity,
                    item.unit_price,
                    order.id,
                    payload.remark,
                    current_user,
                )
                item.received_quantity = self._qty(item.received_quantity + quantity)
            self._recalculate_receive_status(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def create_payment(self, order_id: int, payload: PurchasePaymentCreate, current_user: User) -> PurchaseOrderRead:
        order = self._get_order(order_id)
        self._ensure_confirmed(order, "只有已确认采购单可以付款")
        amount = self._money(payload.amount)
        if amount > order.unpaid_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="付款金额不能超过未付金额")
        try:
            payment = PurchasePayment(
                payment_no=self.repo.next_payment_no(),
                payment_date=payload.payment_date,
                amount=amount,
                method=payload.method,
                remark=payload.remark,
                created_by_id=current_user.id,
            )
            order.payments.append(payment)
            order.supplier.current_payable = self._money(order.supplier.current_payable - amount)
            self.db.flush()
            self._recalculate_order(order)
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def cancel_order(self, order_id: int, payload: PurchaseCancelCreate, current_user: User) -> PurchaseOrderRead:
        order = self._get_order(order_id)
        if order.status == "cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="采购单已作废")
        if order.paid_amount > ZERO_MONEY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="第一版暂不支持作废已付款采购单")
        try:
            if order.status == "confirmed":
                for movement in self.repo.get_purchase_in_movements(order.id):
                    self.inventory_service.record_purchase_cancel_reverse(
                        movement.product,
                        order.warehouse,
                        movement.quantity,
                        order.id,
                        payload.reason,
                        current_user,
                    )
                order.supplier.current_payable = self._money(order.supplier.current_payable - order.unpaid_amount)
            order.status = "cancelled"
            order.cancelled_by_id = current_user.id
            order.cancelled_at = datetime.now(timezone.utc)
            order.cancel_reason = payload.reason
            self.db.commit()
            return self.get_order(order.id)
        except Exception:
            self.db.rollback()
            raise

    def _build_item(self, payload: PurchaseOrderItemCreate) -> PurchaseOrderItem:
        product = self._get_product(payload.product_id)
        quantity = self._qty(payload.quantity)
        unit_price = self._money(payload.unit_price)
        discount = self._money(payload.discount_amount)
        line_amount = self._money(quantity * unit_price - discount)
        if line_amount < ZERO_MONEY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="明细金额不能小于 0")
        return PurchaseOrderItem(
            product_id=product.id,
            product_code=product.code,
            product_name=product.name,
            product_barcode=product.barcode,
            product_spec=product.spec,
            product_model=product.model,
            unit_name=product.unit.name if product.unit else None,
            quantity=quantity,
            received_quantity=ZERO_QTY,
            unit_price=unit_price,
            discount_amount=discount,
            line_amount=line_amount,
            remark=payload.remark,
        )

    def _recalculate_order(self, order: PurchaseOrder) -> None:
        order.total_quantity = self._qty(sum((item.quantity for item in order.items), ZERO_QTY))
        order.total_amount = self._money(sum((item.line_amount for item in order.items), ZERO_MONEY))
        order.discount_amount = self._money(order.discount_amount)
        order.payable_amount = self._money(order.total_amount - order.discount_amount)
        if order.payable_amount < ZERO_MONEY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="整单应付金额不能小于 0")
        order.paid_amount = self._money(sum((payment.amount for payment in order.payments), ZERO_MONEY))
        order.unpaid_amount = self._money(order.payable_amount - order.paid_amount)
        self._recalculate_receive_status(order)
        self._recalculate_payment_status(order)

    def _recalculate_receive_status(self, order: PurchaseOrder) -> None:
        if all(item.received_quantity == ZERO_QTY for item in order.items):
            order.receive_status = "not_received"
        elif all(item.received_quantity >= item.quantity for item in order.items):
            order.receive_status = "received"
        else:
            order.receive_status = "partial_received"

    def _recalculate_payment_status(self, order: PurchaseOrder) -> None:
        if order.paid_amount == ZERO_MONEY:
            order.payment_status = "unpaid"
        elif order.paid_amount < order.payable_amount:
            order.payment_status = "partial_paid"
        else:
            order.payment_status = "paid"

    def _get_order(self, order_id: int) -> PurchaseOrder:
        order = self.repo.get_order(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="采购单不存在")
        return order

    def _get_supplier(self, supplier_id: int) -> Supplier:
        supplier = self.repo.get_supplier(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商不存在或已禁用")
        return supplier

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

    def _ensure_confirmed(self, order: PurchaseOrder, message: str) -> None:
        if order.status != "confirmed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    def _to_list_item(self, order: PurchaseOrder) -> PurchaseOrderListItem:
        return PurchaseOrderListItem(
            id=order.id,
            order_no=order.order_no,
            order_date=order.order_date,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier.name,
            status=order.status,
            receive_status=order.receive_status,
            payment_status=order.payment_status,
            total_quantity=order.total_quantity,
            payable_amount=order.payable_amount,
            paid_amount=order.paid_amount,
            unpaid_amount=order.unpaid_amount,
            created_at=order.created_at,
        )

    def _to_read(self, order: PurchaseOrder) -> PurchaseOrderRead:
        base = self._to_list_item(order).model_dump()
        return PurchaseOrderRead(
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
                    "received_quantity": item.received_quantity,
                    "unit_price": item.unit_price,
                    "discount_amount": item.discount_amount,
                    "line_amount": item.line_amount,
                    "remark": item.remark,
                }
                for item in order.items
            ],
            payments=[
                PurchasePaymentRead(
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
