from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.print_templates.model import PrintSetting
from app.modules.purchase.model import PurchaseOrder, PurchaseOrderItem, PurchasePayment
from app.modules.sales.model import SalesOrder, SalesOrderItem, SalesPayment


class PrintTemplateRepository:
    """第 11 阶段新增：打印配置和打印数据查询集中放在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_settings(self) -> list[PrintSetting]:
        return list(self.db.scalars(select(PrintSetting).order_by(PrintSetting.id)).all())

    def get_setting(self, doc_type: str) -> PrintSetting | None:
        return self.db.scalar(select(PrintSetting).where(PrintSetting.doc_type == doc_type))

    def add_setting(self, setting: PrintSetting) -> PrintSetting:
        self.db.add(setting)
        self.db.flush()
        return setting

    def get_sales_order(self, order_id: int) -> SalesOrder | None:
        return self.db.scalar(
            select(SalesOrder)
            .options(
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.warehouse),
                joinedload(SalesOrder.created_by),
                selectinload(SalesOrder.items).joinedload(SalesOrderItem.product),
                selectinload(SalesOrder.payments).joinedload(SalesPayment.created_by),
            )
            .where(SalesOrder.id == order_id)
        )

    def get_purchase_order(self, order_id: int) -> PurchaseOrder | None:
        return self.db.scalar(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.warehouse),
                joinedload(PurchaseOrder.created_by),
                selectinload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
                selectinload(PurchaseOrder.payments).joinedload(PurchasePayment.created_by),
            )
            .where(PurchaseOrder.id == order_id)
        )

