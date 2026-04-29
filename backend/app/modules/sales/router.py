from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.sales.schemas import (
    SalesCancelCreate,
    SalesOrderCreate,
    SalesOrderListResponse,
    SalesOrderRead,
    SalesOrderUpdate,
    SalesPaymentCreate,
    SalesShipCreate,
)
from app.modules.sales.service import SalesService
from app.modules.users.model import User

router = APIRouter()


@router.get("/sales-orders", response_model=SalesOrderListResponse)
def list_sales_orders(
    keyword: str | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    delivery_status: str | None = None,
    payment_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderListResponse:
    return SalesService(db).list_orders(
        keyword,
        customer_id,
        status,
        delivery_status,
        payment_status,
        start_date,
        end_date,
        page,
        page_size,
    )


@router.post("/sales-orders", response_model=SalesOrderRead)
def create_sales_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).create_order(payload, current_user)


@router.get("/sales-orders/{order_id}", response_model=SalesOrderRead)
def get_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).get_order(order_id)


@router.put("/sales-orders/{order_id}", response_model=SalesOrderRead)
def update_sales_order(
    order_id: int,
    payload: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).update_order(order_id, payload)


@router.post("/sales-orders/{order_id}/confirm", response_model=SalesOrderRead)
def confirm_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).confirm_order(order_id, current_user)


@router.post("/sales-orders/{order_id}/ship", response_model=SalesOrderRead)
def ship_sales_order(
    order_id: int,
    payload: SalesShipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).ship_order(order_id, payload, current_user)


@router.post("/sales-orders/{order_id}/payments", response_model=SalesOrderRead)
def create_sales_payment(
    order_id: int,
    payload: SalesPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).create_payment(order_id, payload, current_user)


@router.post("/sales-orders/{order_id}/cancel", response_model=SalesOrderRead)
def cancel_sales_order(
    order_id: int,
    payload: SalesCancelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderRead:
    return SalesService(db).cancel_order(order_id, payload, current_user)
