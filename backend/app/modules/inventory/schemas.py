from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class InventoryDecimalMixin(BaseModel):
    @field_serializer("quantity_on_hand", "stock_warning_qty", "quantity", "before_qty", "after_qty", check_fields=False)
    def serialize_quantity(self, value: Decimal) -> str:
        return f"{value:.3f}"

    @field_serializer("average_cost", "unit_cost", "before_avg_cost", "after_avg_cost", check_fields=False)
    def serialize_cost(self, value: Decimal) -> str:
        return f"{value:.4f}"

    @field_serializer("total_cost", "amount", check_fields=False)
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"


class WarehouseRead(BaseModel):
    id: int
    name: str
    sort_order: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryRead(InventoryDecimalMixin):
    product_id: int
    product_code: str | None = None
    barcode: str | None = None
    product_name: str
    category_id: int | None = None
    category_name: str | None = None
    unit_id: int | None = None
    unit_name: str | None = None
    spec: str | None = None
    model: str | None = None
    brand: str | None = None
    warehouse_id: int
    warehouse_name: str
    quantity_on_hand: Decimal
    average_cost: Decimal
    total_cost: Decimal
    stock_warning_qty: Decimal
    is_low_stock: bool
    updated_at: datetime | None = None


class InventoryListResponse(BaseModel):
    items: list[InventoryRead]
    total: int
    page: int
    page_size: int


class InitialStockCreate(BaseModel):
    product_id: int
    warehouse_id: int | None = None
    quantity: Decimal = Field(ge=Decimal("0.000"))
    unit_cost: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    remark: str | None = None


class InventoryAdjustmentCreate(BaseModel):
    product_id: int
    warehouse_id: int | None = None
    mode: Literal["increase", "decrease", "set"]
    quantity: Decimal | None = Field(default=None, gt=Decimal("0.000"))
    target_qty: Decimal | None = Field(default=None, ge=Decimal("0.000"))
    unit_cost: Decimal | None = Field(default=None, ge=Decimal("0.0000"))
    remark: str | None = None


class StockMovementRead(InventoryDecimalMixin):
    id: int
    movement_no: str
    product_id: int
    product_code: str | None = None
    barcode: str | None = None
    product_name: str
    warehouse_id: int
    warehouse_name: str
    movement_type: str
    direction: str
    quantity: Decimal
    unit_cost: Decimal
    amount: Decimal
    before_qty: Decimal
    after_qty: Decimal
    before_avg_cost: Decimal
    after_avg_cost: Decimal
    source_type: str
    source_id: int | None = None
    remark: str | None = None
    created_by_id: int | None = None
    created_by_name: str | None = None
    created_at: datetime


class StockMovementListResponse(BaseModel):
    items: list[StockMovementRead]
    total: int
    page: int
    page_size: int
