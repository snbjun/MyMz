from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.permissions import Permission, require_permission
from app.modules.reports.schemas import (
    FinanceByCategoryResponse,
    FinanceSummary,
    InventoryMovementSummary,
    InventorySummary,
    OverviewResponse,
    PayableResponse,
    ProfitSummary,
    PurchaseByProductResponse,
    PurchaseBySupplierResponse,
    PurchaseSummary,
    ReceivableResponse,
    SalesByCustomerResponse,
    SalesByProductResponse,
    SalesSummary,
)
from app.modules.reports.service import ReportService

router = APIRouter(prefix="/reports")

require_reports_view = require_permission(Permission.REPORTS_VIEW)


@router.get("/overview", response_model=OverviewResponse)
def overview(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> OverviewResponse:
    return ReportService(db).overview(start_date, end_date)


@router.get("/sales/summary", response_model=SalesSummary)
def sales_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> SalesSummary:
    return ReportService(db).sales_summary(start_date, end_date)


@router.get("/sales/by-customer", response_model=SalesByCustomerResponse)
def sales_by_customer(
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> SalesByCustomerResponse:
    return ReportService(db).sales_by_customer(start_date, end_date, page, page_size)


@router.get("/sales/by-product", response_model=SalesByProductResponse)
def sales_by_product(
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> SalesByProductResponse:
    return ReportService(db).sales_by_product(start_date, end_date, page, page_size)


@router.get("/purchase/summary", response_model=PurchaseSummary)
def purchase_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> PurchaseSummary:
    return ReportService(db).purchase_summary(start_date, end_date)


@router.get("/purchase/by-supplier", response_model=PurchaseBySupplierResponse)
def purchase_by_supplier(
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> PurchaseBySupplierResponse:
    return ReportService(db).purchase_by_supplier(start_date, end_date, page, page_size)


@router.get("/purchase/by-product", response_model=PurchaseByProductResponse)
def purchase_by_product(
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> PurchaseByProductResponse:
    return ReportService(db).purchase_by_product(start_date, end_date, page, page_size)


@router.get("/receivables", response_model=ReceivableResponse)
def receivables(
    keyword: str | None = None,
    include_zero: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> ReceivableResponse:
    return ReportService(db).receivables(keyword, include_zero, page, page_size)


@router.get("/payables", response_model=PayableResponse)
def payables(
    keyword: str | None = None,
    include_zero: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> PayableResponse:
    return ReportService(db).payables(keyword, include_zero, page, page_size)


@router.get("/inventory/summary", response_model=InventorySummary)
def inventory_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> InventorySummary:
    return ReportService(db).inventory_summary()


@router.get("/inventory/movement-summary", response_model=InventoryMovementSummary)
def inventory_movement_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> InventoryMovementSummary:
    return ReportService(db).inventory_movement_summary(start_date, end_date)


@router.get("/finance/summary", response_model=FinanceSummary)
def finance_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> FinanceSummary:
    return ReportService(db).finance_summary(start_date, end_date)


@router.get("/finance/by-category", response_model=FinanceByCategoryResponse)
def finance_by_category(
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> FinanceByCategoryResponse:
    return ReportService(db).finance_by_category(start_date, end_date, page, page_size)


@router.get("/profit", response_model=ProfitSummary)
def profit(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_reports_view),
) -> ProfitSummary:
    return ReportService(db).profit(start_date, end_date)
