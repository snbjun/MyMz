from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.suppliers.model import Supplier, SupplierCategory
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import (
    SupplierCategoryCreate,
    SupplierCategoryUpdate,
    SupplierCreate,
    SupplierListResponse,
    SupplierUpdate,
)


class SupplierService:
    """第 4 阶段新增：供应商分类与供应商档案业务规则。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SupplierRepository(db)

    def list_categories(self) -> list[SupplierCategory]:
        return self.repo.list_categories()

    def create_category(self, payload: SupplierCategoryCreate) -> SupplierCategory:
        if self.repo.get_category_by_name(payload.name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商分类名称已存在")
        if payload.is_default:
            self._clear_default_categories()
        category = SupplierCategory(
            name=payload.name,
            sort_order=payload.sort_order,
            is_default=payload.is_default,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category_id: int, payload: SupplierCategoryUpdate) -> SupplierCategory:
        category = self._get_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and self.repo.has_other_category_with_name(data["name"], category_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商分类名称已存在")
        if data.get("is_default") is True:
            self._clear_default_categories(exclude_category_id=category_id)
        if category.is_default and data.get("is_default") is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消默认分类")
        for field, value in data.items():
            setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self._get_category(category_id)
        if category.is_default or self.repo.count_active_categories(exclude_category_id=category_id) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除默认分类")
        if self.repo.count_suppliers_by_category(category_id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类正在被供应商使用，不能删除")
        self.repo.soft_delete_category(category)
        self.db.commit()

    def list_suppliers(
        self,
        keyword: str | None,
        category_id: int | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> SupplierListResponse:
        items, total = self.repo.list_suppliers(keyword, category_id, is_active, page, page_size)
        return SupplierListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_supplier(self, supplier_id: int) -> Supplier:
        supplier = self.repo.get_supplier(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供应商不存在或已删除")
        return supplier

    def create_supplier(self, payload: SupplierCreate) -> Supplier:
        if self.repo.get_supplier_by_name(payload.name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商名称已存在")
        self._ensure_category_exists(payload.category_id)
        current_payable = payload.current_payable
        if current_payable is None:
            current_payable = payload.opening_payable
        supplier = Supplier(
            code=payload.code,
            name=payload.name,
            category_id=payload.category_id,
            contact_name=payload.contact_name,
            phone=payload.phone,
            backup_phone=payload.backup_phone,
            email=payload.email,
            wechat=payload.wechat,
            address=payload.address,
            tax_number=payload.tax_number,
            opening_payable=payload.opening_payable,
            current_payable=current_payable,
            credit_limit=payload.credit_limit,
            remark=payload.remark,
            is_active=payload.is_active,
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return self.get_supplier(supplier.id)

    def update_supplier(self, supplier_id: int, payload: SupplierUpdate) -> Supplier:
        supplier = self.get_supplier(supplier_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] and self.repo.has_other_supplier_with_name(data["name"], supplier_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商名称已存在")
        if "category_id" in data:
            self._ensure_category_exists(data["category_id"])
        for money_field in ("opening_payable", "current_payable", "credit_limit"):
            if money_field in data and data[money_field] is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="金额字段不能为空")
        for field, value in data.items():
            setattr(supplier, field, value)
        self.db.commit()
        self.db.refresh(supplier)
        return self.get_supplier(supplier.id)

    def delete_supplier(self, supplier_id: int) -> None:
        supplier = self.get_supplier(supplier_id)
        self.repo.soft_delete_supplier(supplier)
        self.db.commit()

    def toggle_active(self, supplier_id: int) -> Supplier:
        supplier = self.get_supplier(supplier_id)
        supplier.is_active = not supplier.is_active
        self.db.commit()
        self.db.refresh(supplier)
        return self.get_supplier(supplier.id)

    def _get_category(self, category_id: int) -> SupplierCategory:
        category = self.repo.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供应商分类不存在或已删除")
        return category

    def _ensure_category_exists(self, category_id: int | None) -> None:
        if category_id is not None and self.repo.get_category(category_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="供应商分类不存在或已删除")

    def _clear_default_categories(self, exclude_category_id: int | None = None) -> None:
        for category in self.repo.list_categories():
            if exclude_category_id is None or category.id != exclude_category_id:
                category.is_default = False

