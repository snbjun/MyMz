from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.print_templates.model import PrintSetting
from app.modules.print_templates.repository import PrintTemplateRepository
from app.modules.print_templates.schemas import (
    PrintItemRead,
    PrintPaymentSummary,
    PrintSettingRead,
    PrintSettingUpdate,
    PurchaseOrderPrintData,
    SalesOrderPrintData,
)

DOC_TYPES = {"sales_order", "purchase_order"}


class PrintTemplateService:
    """第 11 阶段新增：打印配置校验和单据打印数据组装。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PrintTemplateRepository(db)

    def list_settings(self) -> list[PrintSettingRead]:
        self._ensure_default_settings()
        return [self._to_setting_read(setting) for setting in self.repo.list_settings()]

    def get_setting(self, doc_type: str) -> PrintSettingRead:
        return self._to_setting_read(self._ensure_setting(doc_type))

    def update_setting(self, doc_type: str, payload: PrintSettingUpdate) -> PrintSettingRead:
        setting = self._ensure_setting(doc_type)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(setting, field, value)
        setting.paper_size = "A4"
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self._to_setting_read(setting)

    def get_sales_order_print_data(self, order_id: int) -> SalesOrderPrintData:
        order = self.repo.get_sales_order(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="销售单不存在")
        setting = self._ensure_setting("sales_order")
        return SalesOrderPrintData(
            order_no=order.order_no,
            order_date=order.order_date,
            status=order.status,
            customer_name=order.customer.name,
            customer_phone=order.customer.phone,
            customer_address=order.customer.address,
            warehouse_name=order.warehouse.name,
            items=[
                PrintItemRead(
                    id=item.id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    product_barcode=item.product_barcode,
                    product_spec=item.product_spec,
                    product_model=item.product_model,
                    unit_name=item.unit_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_amount=item.discount_amount,
                    line_amount=item.line_amount,
                    remark=item.remark,
                )
                for item in order.items
            ],
            total_quantity=order.total_quantity,
            total_amount=order.total_amount,
            discount_amount=order.discount_amount,
            receivable_amount=order.receivable_amount,
            paid_amount=order.paid_amount,
            unpaid_amount=order.unpaid_amount,
            remark=order.remark,
            created_by_name=order.created_by.display_name if order.created_by else None,
            confirmed_at=order.confirmed_at,
            payment_summary=PrintPaymentSummary(count=len(order.payments), amount=sum((p.amount for p in order.payments), Decimal("0.00"))),
            print_settings=self._to_setting_read(setting),
        )

    def get_purchase_order_print_data(self, order_id: int) -> PurchaseOrderPrintData:
        order = self.repo.get_purchase_order(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="采购单不存在")
        setting = self._ensure_setting("purchase_order")
        return PurchaseOrderPrintData(
            order_no=order.order_no,
            order_date=order.order_date,
            status=order.status,
            supplier_name=order.supplier.name,
            supplier_phone=order.supplier.phone,
            supplier_address=order.supplier.address,
            warehouse_name=order.warehouse.name,
            items=[
                PrintItemRead(
                    id=item.id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    product_barcode=item.product_barcode,
                    product_spec=item.product_spec,
                    product_model=item.product_model,
                    unit_name=item.unit_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_amount=item.discount_amount,
                    line_amount=item.line_amount,
                    remark=item.remark,
                )
                for item in order.items
            ],
            total_quantity=order.total_quantity,
            total_amount=order.total_amount,
            discount_amount=order.discount_amount,
            payable_amount=order.payable_amount,
            paid_amount=order.paid_amount,
            unpaid_amount=order.unpaid_amount,
            remark=order.remark,
            created_by_name=order.created_by.display_name if order.created_by else None,
            confirmed_at=order.confirmed_at,
            payment_summary=PrintPaymentSummary(count=len(order.payments), amount=sum((p.amount for p in order.payments), Decimal("0.00"))),
            print_settings=self._to_setting_read(setting),
        )

    def _ensure_default_settings(self) -> None:
        for doc_type in DOC_TYPES:
            self._ensure_setting(doc_type)

    def _ensure_setting(self, doc_type: str) -> PrintSetting:
        if doc_type not in DOC_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法打印单据类型")
        setting = self.repo.get_setting(doc_type)
        if setting is not None:
            return setting
        setting = self.repo.add_setting(self._default_setting(doc_type))
        self.db.commit()
        return setting

    def _default_setting(self, doc_type: str) -> PrintSetting:
        return PrintSetting(
            doc_type=doc_type,
            template_name="标准模板",
            paper_size="A4",
            show_company_name=True,
            company_name="",
            show_contact=False,
            contact_text="",
            show_amount=True,
            show_unit_price=True,
            show_discount=True,
            show_remark=True,
            show_signature=True,
            footer_text="",
            is_default=True,
        )

    def _to_setting_read(self, setting: PrintSetting) -> PrintSettingRead:
        return PrintSettingRead(
            id=setting.id,
            doc_type=setting.doc_type,  # type: ignore[arg-type]
            template_name=setting.template_name,
            paper_size=setting.paper_size,
            show_company_name=setting.show_company_name,
            company_name=setting.company_name,
            show_contact=setting.show_contact,
            contact_text=setting.contact_text,
            show_amount=setting.show_amount,
            show_unit_price=setting.show_unit_price,
            show_discount=setting.show_discount,
            show_remark=setting.show_remark,
            show_signature=setting.show_signature,
            footer_text=setting.footer_text,
            is_default=setting.is_default,
            created_at=setting.created_at,
            updated_at=setting.updated_at,
        )

