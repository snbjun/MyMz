from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.print_templates.schemas import (
    PrintSettingRead,
    PrintSettingUpdate,
    PurchaseOrderPrintData,
    SalesOrderPrintData,
)
from app.modules.print_templates.service import PrintTemplateService
from app.modules.users.model import User

router = APIRouter()


@router.get("/print-settings", response_model=list[PrintSettingRead])
def list_print_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PrintSettingRead]:
    return PrintTemplateService(db).list_settings()


@router.get("/print-settings/{doc_type}", response_model=PrintSettingRead)
def get_print_setting(
    doc_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrintSettingRead:
    return PrintTemplateService(db).get_setting(doc_type)


@router.put("/print-settings/{doc_type}", response_model=PrintSettingRead)
def update_print_setting(
    doc_type: str,
    payload: PrintSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrintSettingRead:
    return PrintTemplateService(db).update_setting(doc_type, payload)


@router.get("/print/sales-orders/{order_id}", response_model=SalesOrderPrintData)
def get_sales_order_print_data(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SalesOrderPrintData:
    return PrintTemplateService(db).get_sales_order_print_data(order_id)


@router.get("/print/purchase-orders/{order_id}", response_model=PurchaseOrderPrintData)
def get_purchase_order_print_data(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderPrintData:
    return PrintTemplateService(db).get_purchase_order_print_data(order_id)

