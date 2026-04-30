from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.purchase.schemas import (
    PurchaseCancelCreate,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderRead,
    PurchaseOrderUpdate,
    PurchasePaymentCreate,
    PurchaseReceiveCreate,
)
from app.modules.purchase.service import PurchaseService
from app.modules.users.model import User

router = APIRouter()


@router.get("/purchase-orders", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    keyword: str | None = None,
    supplier_id: int | None = None,
    status: str | None = None,
    receive_status: str | None = None,
    payment_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderListResponse:
    return PurchaseService(db).list_orders(
        keyword,
        supplier_id,
        status,
        receive_status,
        payment_status,
        start_date,
        end_date,
        page,
        page_size,
    )


@router.post("/purchase-orders", response_model=PurchaseOrderRead)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).create_order(payload, current_user)


@router.get("/purchase-orders/{order_id}", response_model=PurchaseOrderRead)
def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).get_order(order_id)


@router.put("/purchase-orders/{order_id}", response_model=PurchaseOrderRead)
def update_purchase_order(
    order_id: int,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).update_order(order_id, payload)


@router.post("/purchase-orders/{order_id}/confirm", response_model=PurchaseOrderRead)
def confirm_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).confirm_order(order_id, current_user)


@router.post("/purchase-orders/{order_id}/receive", response_model=PurchaseOrderRead)
def receive_purchase_order(
    order_id: int,
    payload: PurchaseReceiveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).receive_order(order_id, payload, current_user)


@router.post("/purchase-orders/{order_id}/payments", response_model=PurchaseOrderRead)
def create_purchase_payment(
    order_id: int,
    payload: PurchasePaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).create_payment(order_id, payload, current_user)


@router.post("/purchase-orders/{order_id}/cancel", response_model=PurchaseOrderRead)
def cancel_purchase_order(
    order_id: int,
    payload: PurchaseCancelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    return PurchaseService(db).cancel_order(order_id, payload, current_user)
