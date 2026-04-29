from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.inventory.model import Inventory, StockMovement, Warehouse
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    InitialStockCreate,
    InventoryAdjustmentCreate,
    InventoryListResponse,
    InventoryRead,
    StockMovementListResponse,
    StockMovementRead,
)
from app.modules.products.model import Product
from app.modules.users.model import User

QTY = Decimal("0.001")
COST = Decimal("0.0001")
MONEY = Decimal("0.01")
ZERO_QTY = Decimal("0.000")
ZERO_COST = Decimal("0.0000")
ZERO_MONEY = Decimal("0.00")


class InventoryService:
    """第 6 阶段新增：库存业务规则、成本计算和库存流水统一封装在 service。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InventoryRepository(db)

    def list_warehouses(self) -> list[Warehouse]:
        return self.repo.list_active_warehouses()

    def list_inventory(
        self,
        keyword: str | None,
        category_id: int | None,
        warehouse_id: int | None,
        low_stock_only: bool,
        page: int,
        page_size: int,
    ) -> InventoryListResponse:
        warehouse = self._get_warehouse_or_default(warehouse_id)
        items, total = self.repo.list_inventory(warehouse, keyword, category_id, low_stock_only, page, page_size)
        return InventoryListResponse(items=[InventoryRead(**item) for item in items], total=total, page=page, page_size=page_size)

    def get_inventory(self, product_id: int, warehouse_id: int | None = None) -> InventoryRead:
        product = self._get_product(product_id)
        warehouse = self._get_warehouse_or_default(warehouse_id)
        return InventoryRead(**self.repo.get_inventory_detail(product, warehouse))

    def set_initial_stock(self, payload: InitialStockCreate, current_user: User) -> InventoryRead:
        product = self._get_product(payload.product_id)
        warehouse = self._get_warehouse_or_default(payload.warehouse_id)
        quantity = self._qty(payload.quantity)
        unit_cost = self._cost(payload.unit_cost)
        if self.repo.count_movements_for_product_warehouse(product.id, warehouse.id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该产品已有库存流水，不能重复设置期初库存")
        try:
            inventory = self.repo.get_or_create_inventory(product.id, warehouse.id)
            inventory.quantity_on_hand = quantity
            inventory.average_cost = unit_cost if quantity > ZERO_QTY else ZERO_COST
            inventory.total_cost = self._money(quantity * inventory.average_cost)
            if quantity > ZERO_QTY:
                self._create_movement(
                    product=product,
                    warehouse=warehouse,
                    inventory=inventory,
                    movement_type="initial",
                    direction="in",
                    quantity=quantity,
                    unit_cost=unit_cost,
                    before_qty=ZERO_QTY,
                    after_qty=quantity,
                    before_avg_cost=ZERO_COST,
                    after_avg_cost=inventory.average_cost,
                    source_type="manual_initial",
                    source_id=None,
                    remark=payload.remark,
                    current_user=current_user,
                )
            self.db.commit()
            return self.get_inventory(product.id, warehouse.id)
        except Exception:
            self.db.rollback()
            raise

    def adjust_inventory(self, payload: InventoryAdjustmentCreate, current_user: User) -> InventoryRead:
        product = self._get_product(payload.product_id)
        warehouse = self._get_warehouse_or_default(payload.warehouse_id)
        try:
            inventory = self.repo.get_or_create_inventory(product.id, warehouse.id)
            before_qty = self._qty(inventory.quantity_on_hand)
            before_avg_cost = self._cost(inventory.average_cost)

            if payload.mode == "increase":
                if payload.quantity is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="增加库存必须填写调整数量")
                self._apply_increase(product, warehouse, inventory, self._qty(payload.quantity), payload.unit_cost, "adjustment_in", "manual_adjustment", payload.remark, current_user)
            elif payload.mode == "decrease":
                if payload.quantity is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="减少库存必须填写调整数量")
                self._apply_decrease(product, warehouse, inventory, self._qty(payload.quantity), "adjustment_out", "manual_adjustment", payload.remark, current_user)
            else:
                if payload.target_qty is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="盘点设定必须填写目标库存")
                target_qty = self._qty(payload.target_qty)
                diff_qty = self._qty(target_qty - before_qty)
                if diff_qty == ZERO_QTY:
                    self.db.commit()
                    return self.get_inventory(product.id, warehouse.id)
                if diff_qty > ZERO_QTY:
                    self._apply_increase(product, warehouse, inventory, diff_qty, payload.unit_cost, "stocktaking_gain", "stocktaking", payload.remark, current_user)
                else:
                    self._apply_decrease(product, warehouse, inventory, abs(diff_qty), "stocktaking_loss", "stocktaking", payload.remark, current_user)
            self.db.commit()
            return self.get_inventory(product.id, warehouse.id)
        except Exception:
            self.db.rollback()
            raise

    def list_movements(
        self,
        keyword: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        movement_type: str | None,
        direction: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> StockMovementListResponse:
        items, total = self.repo.list_movements(
            keyword, product_id, warehouse_id, movement_type, direction, start_date, end_date, page, page_size
        )
        return StockMovementListResponse(items=[self._movement_to_schema(item) for item in items], total=total, page=page, page_size=page_size)

    def get_movement(self, movement_id: int) -> StockMovementRead:
        movement = self.repo.get_movement(movement_id)
        if movement is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="库存流水不存在")
        return self._movement_to_schema(movement)

    def _apply_increase(
        self,
        product: Product,
        warehouse: Warehouse,
        inventory: Inventory,
        quantity: Decimal,
        unit_cost: Decimal | None,
        movement_type: str,
        source_type: str,
        remark: str | None,
        current_user: User,
    ) -> None:
        if quantity <= ZERO_QTY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="入库数量必须大于 0")
        before_qty = self._qty(inventory.quantity_on_hand)
        before_avg_cost = self._cost(inventory.average_cost)
        cost = self._cost(unit_cost if unit_cost is not None else product.purchase_price or ZERO_COST)
        after_qty = self._qty(before_qty + quantity)
        if after_qty <= ZERO_QTY:
            after_avg_cost = ZERO_COST
        else:
            after_avg_cost = self._cost(((before_qty * before_avg_cost) + (quantity * cost)) / after_qty)
        inventory.quantity_on_hand = after_qty
        inventory.average_cost = after_avg_cost
        inventory.total_cost = self._money(after_qty * after_avg_cost)
        self._create_movement(
            product,
            warehouse,
            inventory,
            movement_type,
            "in",
            quantity,
            cost,
            before_qty,
            after_qty,
            before_avg_cost,
            after_avg_cost,
            source_type,
            None,
            remark,
            current_user,
        )

    def _apply_decrease(
        self,
        product: Product,
        warehouse: Warehouse,
        inventory: Inventory,
        quantity: Decimal,
        movement_type: str,
        source_type: str,
        remark: str | None,
        current_user: User,
    ) -> None:
        if quantity <= ZERO_QTY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="出库数量必须大于 0")
        before_qty = self._qty(inventory.quantity_on_hand)
        before_avg_cost = self._cost(inventory.average_cost)
        after_qty = self._qty(before_qty - quantity)
        if after_qty < ZERO_QTY:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足，调整后库存不能为负数")
        after_avg_cost = ZERO_COST if after_qty == ZERO_QTY else before_avg_cost
        inventory.quantity_on_hand = after_qty
        inventory.average_cost = after_avg_cost
        inventory.total_cost = self._money(after_qty * after_avg_cost)
        self._create_movement(
            product,
            warehouse,
            inventory,
            movement_type,
            "out",
            quantity,
            before_avg_cost,
            before_qty,
            after_qty,
            before_avg_cost,
            after_avg_cost,
            source_type,
            None,
            remark,
            current_user,
        )

    def _create_movement(
        self,
        product: Product,
        warehouse: Warehouse,
        inventory: Inventory,
        movement_type: str,
        direction: str,
        quantity: Decimal,
        unit_cost: Decimal,
        before_qty: Decimal,
        after_qty: Decimal,
        before_avg_cost: Decimal,
        after_avg_cost: Decimal,
        source_type: str,
        source_id: int | None,
        remark: str | None,
        current_user: User,
    ) -> StockMovement:
        amount = self._money(quantity * unit_cost)
        movement = StockMovement(
            movement_no=self.repo.next_movement_no(),
            product_id=product.id,
            warehouse_id=warehouse.id,
            movement_type=movement_type,
            direction=direction,
            quantity=self._qty(quantity),
            unit_cost=self._cost(unit_cost),
            amount=amount,
            before_qty=self._qty(before_qty),
            after_qty=self._qty(after_qty),
            before_avg_cost=self._cost(before_avg_cost),
            after_avg_cost=self._cost(after_avg_cost),
            source_type=source_type,
            source_id=source_id,
            remark=remark,
            created_by_id=current_user.id,
        )
        return self.repo.create_movement(movement)

    def _get_warehouse_or_default(self, warehouse_id: int | None) -> Warehouse:
        warehouse = self.repo.get_warehouse(warehouse_id) if warehouse_id is not None else self.repo.get_default_warehouse()
        if warehouse is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="仓库不存在或已停用")
        return warehouse

    def _get_product(self, product_id: int) -> Product:
        product = self.repo.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在或已删除")
        return product

    def _movement_to_schema(self, movement: StockMovement) -> StockMovementRead:
        return StockMovementRead(
            id=movement.id,
            movement_no=movement.movement_no,
            product_id=movement.product_id,
            product_code=movement.product.code if movement.product else None,
            barcode=movement.product.barcode if movement.product else None,
            product_name=movement.product.name if movement.product else "",
            warehouse_id=movement.warehouse_id,
            warehouse_name=movement.warehouse.name if movement.warehouse else "",
            movement_type=movement.movement_type,
            direction=movement.direction,
            quantity=movement.quantity,
            unit_cost=movement.unit_cost,
            amount=movement.amount,
            before_qty=movement.before_qty,
            after_qty=movement.after_qty,
            before_avg_cost=movement.before_avg_cost,
            after_avg_cost=movement.after_avg_cost,
            source_type=movement.source_type,
            source_id=movement.source_id,
            remark=movement.remark,
            created_by_id=movement.created_by_id,
            created_by_name=movement.created_by.display_name if movement.created_by else None,
            created_at=movement.created_at,
        )

    def _qty(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(QTY, rounding=ROUND_HALF_UP)

    def _cost(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(COST, rounding=ROUND_HALF_UP)

    def _money(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)
