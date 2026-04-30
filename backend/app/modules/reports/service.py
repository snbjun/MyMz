from datetime import date

from sqlalchemy.orm import Session

from app.modules.reports.repository import ReportRepository
from app.modules.reports.schemas import (
    FinanceByCategoryResponse,
    FinanceSummary,
    InventoryMovementSummary,
    InventorySummary,
    OverviewResponse,
    PayableResponse,
    PayableSummary,
    ProfitSummary,
    PurchaseByProductResponse,
    PurchaseBySupplierResponse,
    PurchaseSummary,
    ReceivableResponse,
    ReceivableSummary,
    SalesByCustomerResponse,
    SalesByProductResponse,
    SalesSummary,
)


class ReportService:
    """第 10 阶段新增：报表统计口径集中在 service，接口保持只读。"""

    def __init__(self, db: Session) -> None:
        self.repo = ReportRepository(db)

    def overview(self, start_date: date | None, end_date: date | None) -> OverviewResponse:
        start, end = self._date_range(start_date, end_date)
        sales = self.sales_summary(start, end)
        purchase = self.purchase_summary(start, end)
        receivable = self.receivable_summary()
        payable = self.payable_summary()
        inventory = self.inventory_summary()
        finance = self.finance_summary(start, end)
        profit = self.profit(start, end)
        return OverviewResponse(
            start_date=start,
            end_date=end,
            sales_summary=sales,
            purchase_summary=purchase,
            receivable_summary=receivable,
            payable_summary=payable,
            inventory_summary=inventory,
            finance_summary=finance,
            profit_summary=profit,
        )

    def sales_summary(self, start_date: date | None, end_date: date | None) -> SalesSummary:
        start, end = self._date_range(start_date, end_date)
        return SalesSummary(**self.repo.sales_summary(start, end))

    def sales_by_customer(self, start_date: date | None, end_date: date | None, page: int, page_size: int) -> SalesByCustomerResponse:
        start, end = self._date_range(start_date, end_date)
        items, total = self.repo.sales_by_customer(start, end, page, page_size)
        return SalesByCustomerResponse(items=items, total=total, page=page, page_size=page_size)

    def sales_by_product(self, start_date: date | None, end_date: date | None, page: int, page_size: int) -> SalesByProductResponse:
        start, end = self._date_range(start_date, end_date)
        items, total = self.repo.sales_by_product(start, end, page, page_size)
        return SalesByProductResponse(items=items, total=total, page=page, page_size=page_size)

    def purchase_summary(self, start_date: date | None, end_date: date | None) -> PurchaseSummary:
        start, end = self._date_range(start_date, end_date)
        return PurchaseSummary(**self.repo.purchase_summary(start, end))

    def purchase_by_supplier(
        self, start_date: date | None, end_date: date | None, page: int, page_size: int
    ) -> PurchaseBySupplierResponse:
        start, end = self._date_range(start_date, end_date)
        items, total = self.repo.purchase_by_supplier(start, end, page, page_size)
        return PurchaseBySupplierResponse(items=items, total=total, page=page, page_size=page_size)

    def purchase_by_product(
        self, start_date: date | None, end_date: date | None, page: int, page_size: int
    ) -> PurchaseByProductResponse:
        start, end = self._date_range(start_date, end_date)
        items, total = self.repo.purchase_by_product(start, end, page, page_size)
        return PurchaseByProductResponse(items=items, total=total, page=page, page_size=page_size)

    def receivable_summary(self) -> ReceivableSummary:
        return ReceivableSummary(**self.repo.receivable_summary())

    def receivables(self, keyword: str | None, include_zero: bool, page: int, page_size: int) -> ReceivableResponse:
        items, total = self.repo.receivables(keyword, include_zero, page, page_size)
        return ReceivableResponse(items=items, total=total, page=page, page_size=page_size)

    def payable_summary(self) -> PayableSummary:
        return PayableSummary(**self.repo.payable_summary())

    def payables(self, keyword: str | None, include_zero: bool, page: int, page_size: int) -> PayableResponse:
        items, total = self.repo.payables(keyword, include_zero, page, page_size)
        return PayableResponse(items=items, total=total, page=page, page_size=page_size)

    def inventory_summary(self) -> InventorySummary:
        return InventorySummary(**self.repo.inventory_summary())

    def inventory_movement_summary(self, start_date: date | None, end_date: date | None) -> InventoryMovementSummary:
        start, end = self._date_range(start_date, end_date)
        return InventoryMovementSummary(**self.repo.inventory_movement_summary(start, end))

    def finance_summary(self, start_date: date | None, end_date: date | None) -> FinanceSummary:
        start, end = self._date_range(start_date, end_date)
        return FinanceSummary(**self.repo.finance_summary(start, end))

    def finance_by_category(self, start_date: date | None, end_date: date | None, page: int, page_size: int) -> FinanceByCategoryResponse:
        start, end = self._date_range(start_date, end_date)
        items, total = self.repo.finance_by_category(start, end, page, page_size)
        return FinanceByCategoryResponse(items=items, total=total, page=page, page_size=page_size)

    def profit(self, start_date: date | None, end_date: date | None) -> ProfitSummary:
        start, end = self._date_range(start_date, end_date)
        sales = self.repo.sales_summary(start, end)
        purchase = self.repo.purchase_summary(start, end)
        finance = self.repo.finance_summary(start, end)
        sales_amount = sales["receivable_amount"]
        purchase_amount = purchase["payable_amount"]
        gross_profit = sales_amount - purchase_amount
        finance_net = finance["net_amount"]
        return ProfitSummary(
            sales_amount=sales_amount,
            purchase_amount=purchase_amount,
            gross_profit=gross_profit,
            income_amount=finance["income_amount"],
            expense_amount=finance["expense_amount"],
            finance_net_amount=finance_net,
            estimated_net_profit=gross_profit + finance_net,
        )

    def _date_range(self, start_date: date | None, end_date: date | None) -> tuple[date, date]:
        today = date.today()
        end = end_date or today
        start = start_date or date(end.year, end.month, 1)
        return start, end
