from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class ReportDecimalMixin(BaseModel):
    @field_serializer(
        "sales_amount",
        "purchase_amount",
        "receivable_amount",
        "paid_amount",
        "unpaid_amount",
        "payable_amount",
        "total_receivable",
        "total_payable",
        "total_cost",
        "stock_amount",
        "balance_total",
        "current_balance",
        "opening_balance",
        "income_amount",
        "expense_amount",
        "in_amount",
        "out_amount",
        "net_amount",
        "gross_profit",
        "finance_net_amount",
        "estimated_net_profit",
        "amount",
        check_fields=False,
    )
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @field_serializer("total_quantity", "quantity", "in_quantity", "out_quantity", check_fields=False)
    def serialize_quantity(self, value: Decimal) -> str:
        return f"{value:.3f}"


class SalesSummary(ReportDecimalMixin):
    order_count: int
    total_quantity: Decimal
    receivable_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal


class SalesByCustomerItem(ReportDecimalMixin):
    customer_id: int
    customer_name: str
    order_count: int
    sales_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal


class SalesByProductItem(ReportDecimalMixin):
    product_id: int
    product_code: str | None = None
    product_name: str
    quantity: Decimal
    sales_amount: Decimal


class PurchaseSummary(ReportDecimalMixin):
    order_count: int
    total_quantity: Decimal
    payable_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal


class PurchaseBySupplierItem(ReportDecimalMixin):
    supplier_id: int
    supplier_name: str
    order_count: int
    purchase_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal


class PurchaseByProductItem(ReportDecimalMixin):
    product_id: int
    product_code: str | None = None
    product_name: str
    quantity: Decimal
    purchase_amount: Decimal


class ReceivableSummary(ReportDecimalMixin):
    customer_count: int
    total_receivable: Decimal


class ReceivableItem(ReportDecimalMixin):
    customer_id: int
    customer_code: str | None = None
    customer_name: str
    phone: str | None = None
    current_receivable: Decimal


class PayableSummary(ReportDecimalMixin):
    supplier_count: int
    total_payable: Decimal


class PayableItem(ReportDecimalMixin):
    supplier_id: int
    supplier_code: str | None = None
    supplier_name: str
    phone: str | None = None
    current_payable: Decimal


class InventorySummary(ReportDecimalMixin):
    product_count: int
    total_quantity: Decimal
    total_cost: Decimal
    low_stock_count: int


class InventoryMovementTypeItem(ReportDecimalMixin):
    movement_type: str
    direction: str
    quantity: Decimal
    amount: Decimal


class InventoryMovementSummary(ReportDecimalMixin):
    in_quantity: Decimal
    out_quantity: Decimal
    in_amount: Decimal
    out_amount: Decimal
    items: list[InventoryMovementTypeItem]


class FinanceAccountBalanceItem(ReportDecimalMixin):
    account_id: int
    account_name: str
    account_type: str
    opening_balance: Decimal
    current_balance: Decimal


class FinanceSummary(ReportDecimalMixin):
    account_count: int
    balance_total: Decimal
    income_amount: Decimal
    expense_amount: Decimal
    net_amount: Decimal
    accounts: list[FinanceAccountBalanceItem]


class FinanceByCategoryItem(ReportDecimalMixin):
    category_id: int
    category_name: str
    type: str
    amount: Decimal


class ProfitSummary(ReportDecimalMixin):
    sales_amount: Decimal
    purchase_amount: Decimal
    gross_profit: Decimal
    income_amount: Decimal
    expense_amount: Decimal
    finance_net_amount: Decimal
    estimated_net_profit: Decimal


class PageResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class SalesByCustomerResponse(BaseModel):
    items: list[SalesByCustomerItem]
    total: int
    page: int
    page_size: int


class SalesByProductResponse(BaseModel):
    items: list[SalesByProductItem]
    total: int
    page: int
    page_size: int


class PurchaseBySupplierResponse(BaseModel):
    items: list[PurchaseBySupplierItem]
    total: int
    page: int
    page_size: int


class PurchaseByProductResponse(BaseModel):
    items: list[PurchaseByProductItem]
    total: int
    page: int
    page_size: int


class ReceivableResponse(BaseModel):
    items: list[ReceivableItem]
    total: int
    page: int
    page_size: int


class PayableResponse(BaseModel):
    items: list[PayableItem]
    total: int
    page: int
    page_size: int


class FinanceByCategoryResponse(BaseModel):
    items: list[FinanceByCategoryItem]
    total: int
    page: int
    page_size: int


class OverviewResponse(BaseModel):
    start_date: date
    end_date: date
    sales_summary: SalesSummary
    purchase_summary: PurchaseSummary
    receivable_summary: ReceivableSummary
    payable_summary: PayableSummary
    inventory_summary: InventorySummary
    finance_summary: FinanceSummary
    profit_summary: ProfitSummary
