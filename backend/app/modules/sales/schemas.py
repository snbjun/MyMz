from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer


class SalesDecimalMixin(BaseModel):
    @field_serializer("total_quantity", "quantity", "shipped_quantity", check_fields=False)
    def serialize_quantity(self, value: Decimal) -> str:
        return f"{value:.3f}"

    @field_serializer(
        "total_amount",
        "discount_amount",
        "receivable_amount",
        "paid_amount",
        "unpaid_amount",
        "unit_price",
        "line_amount",
        "amount",
        check_fields=False,
    )
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"


class SalesOrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    remark: str | None = None


class SalesOrderCreate(BaseModel):
    customer_id: int
    warehouse_id: int | None = None
    order_date: date = Field(default_factory=date.today)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    remark: str | None = None
    items: list[SalesOrderItemCreate] = Field(min_length=1)


class SalesOrderUpdate(SalesOrderCreate):
    pass


class SalesShipItem(BaseModel):
    item_id: int
    quantity: Decimal = Field(gt=0)


class SalesShipCreate(BaseModel):
    items: list[SalesShipItem] = Field(min_length=1)
    remark: str | None = None


class SalesPaymentCreate(BaseModel):
    payment_date: date = Field(default_factory=date.today)
    amount: Decimal = Field(gt=0)
    method: Literal["cash", "wechat", "alipay", "bank", "other"] = "cash"
    remark: str | None = None


class SalesCancelCreate(BaseModel):
    reason: str = Field(min_length=1)


class SalesOrderItemRead(SalesDecimalMixin):
    id: int
    product_id: int
    product_code: str | None = None
    product_name: str
    product_barcode: str | None = None
    product_spec: str | None = None
    product_model: str | None = None
    unit_name: str | None = None
    quantity: Decimal
    shipped_quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    line_amount: Decimal
    remark: str | None = None


class SalesPaymentRead(SalesDecimalMixin):
    id: int
    payment_no: str
    payment_date: date
    amount: Decimal
    method: str
    remark: str | None = None
    created_by_id: int | None = None
    created_by_name: str | None = None
    created_at: datetime


class SalesOrderListItem(SalesDecimalMixin):
    id: int
    order_no: str
    order_date: date
    customer_id: int
    customer_name: str
    status: str
    delivery_status: str
    payment_status: str
    total_quantity: Decimal
    receivable_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal
    created_at: datetime


class SalesOrderRead(SalesOrderListItem):
    warehouse_id: int
    warehouse_name: str
    total_amount: Decimal
    discount_amount: Decimal
    remark: str | None = None
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    updated_at: datetime
    items: list[SalesOrderItemRead]
    payments: list[SalesPaymentRead]


class SalesOrderListResponse(BaseModel):
    items: list[SalesOrderListItem]
    total: int
    page: int
    page_size: int
