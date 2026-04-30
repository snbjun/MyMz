from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

DocType = Literal["sales_order", "purchase_order"]


class PrintSettingRead(BaseModel):
    id: int
    doc_type: DocType
    template_name: str
    paper_size: str
    show_company_name: bool
    company_name: str | None = None
    show_contact: bool
    contact_text: str | None = None
    show_amount: bool
    show_unit_price: bool
    show_discount: bool
    show_remark: bool
    show_signature: bool
    footer_text: str | None = None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class PrintSettingUpdate(BaseModel):
    template_name: str | None = Field(default=None, min_length=1, max_length=64)
    paper_size: Literal["A4"] | None = "A4"
    show_company_name: bool | None = None
    company_name: str | None = None
    show_contact: bool | None = None
    contact_text: str | None = None
    show_amount: bool | None = None
    show_unit_price: bool | None = None
    show_discount: bool | None = None
    show_remark: bool | None = None
    show_signature: bool | None = None
    footer_text: str | None = None


class PrintDecimalMixin(BaseModel):
    @field_serializer("total_quantity", "quantity", check_fields=False)
    def serialize_quantity(self, value: Decimal) -> str:
        return f"{value:.3f}"

    @field_serializer(
        "total_amount",
        "discount_amount",
        "receivable_amount",
        "payable_amount",
        "paid_amount",
        "unpaid_amount",
        "unit_price",
        "line_amount",
        "amount",
        check_fields=False,
    )
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"


class PrintItemRead(PrintDecimalMixin):
    id: int
    product_code: str | None = None
    product_name: str
    product_barcode: str | None = None
    product_spec: str | None = None
    product_model: str | None = None
    unit_name: str | None = None
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    line_amount: Decimal
    remark: str | None = None


class PrintPaymentSummary(PrintDecimalMixin):
    count: int
    amount: Decimal


class SalesOrderPrintData(PrintDecimalMixin):
    order_no: str
    order_date: date
    status: str
    customer_name: str
    customer_phone: str | None = None
    customer_address: str | None = None
    warehouse_name: str
    items: list[PrintItemRead]
    total_quantity: Decimal
    total_amount: Decimal
    discount_amount: Decimal
    receivable_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal
    remark: str | None = None
    created_by_name: str | None = None
    confirmed_at: datetime | None = None
    payment_summary: PrintPaymentSummary
    print_settings: PrintSettingRead


class PurchaseOrderPrintData(PrintDecimalMixin):
    order_no: str
    order_date: date
    status: str
    supplier_name: str
    supplier_phone: str | None = None
    supplier_address: str | None = None
    warehouse_name: str
    items: list[PrintItemRead]
    total_quantity: Decimal
    total_amount: Decimal
    discount_amount: Decimal
    payable_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal
    remark: str | None = None
    created_by_name: str | None = None
    confirmed_at: datetime | None = None
    payment_summary: PrintPaymentSummary
    print_settings: PrintSettingRead

