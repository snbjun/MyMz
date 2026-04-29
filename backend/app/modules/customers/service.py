from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.customers.model import Customer, CustomerCategory
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import (
    CustomerCategoryCreate,
    CustomerCategoryUpdate,
    CustomerCreate,
    CustomerListResponse,
    CustomerUpdate,
)


class CustomerService:
    """第 3 阶段新增：客户分类与客户档案业务规则。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CustomerRepository(db)

    def list_categories(self) -> list[CustomerCategory]:
        return self.repo.list_categories()

    def create_category(self, payload: CustomerCategoryCreate) -> CustomerCategory:
        if self.repo.get_category_by_name(payload.name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="客户分类名称已存在")
        if payload.is_default:
            self._clear_default_categories()
        category = CustomerCategory(
            name=payload.name,
            sort_order=payload.sort_order,
            is_default=payload.is_default,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category_id: int, payload: CustomerCategoryUpdate) -> CustomerCategory:
        category = self._get_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and self.repo.has_other_category_with_name(data["name"], category_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="客户分类名称已存在")
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
        if self.repo.count_customers_by_category(category_id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类正在被客户使用，不能删除")
        self.repo.soft_delete_category(category)
        self.db.commit()

    def list_customers(
        self,
        keyword: str | None,
        category_id: int | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> CustomerListResponse:
        items, total = self.repo.list_customers(keyword, category_id, is_active, page, page_size)
        return CustomerListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在或已删除")
        return customer

    def create_customer(self, payload: CustomerCreate) -> Customer:
        if self.repo.get_customer_by_name(payload.name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="客户名称已存在")
        self._ensure_category_exists(payload.category_id)
        current_receivable = payload.current_receivable
        if current_receivable is None:
            current_receivable = payload.opening_receivable
        customer = Customer(
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
            opening_receivable=payload.opening_receivable,
            current_receivable=current_receivable,
            credit_limit=payload.credit_limit,
            remark=payload.remark,
            is_active=payload.is_active,
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return self.get_customer(customer.id)

    def update_customer(self, customer_id: int, payload: CustomerUpdate) -> Customer:
        customer = self.get_customer(customer_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] and self.repo.has_other_customer_with_name(data["name"], customer_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="客户名称已存在")
        if "category_id" in data:
            self._ensure_category_exists(data["category_id"])
        for money_field in ("opening_receivable", "current_receivable", "credit_limit"):
            if money_field in data and data[money_field] is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="金额字段不能为空")
        for field, value in data.items():
            setattr(customer, field, value)
        self.db.commit()
        self.db.refresh(customer)
        return self.get_customer(customer.id)

    def delete_customer(self, customer_id: int) -> None:
        customer = self.get_customer(customer_id)
        self.repo.soft_delete_customer(customer)
        self.db.commit()

    def toggle_active(self, customer_id: int) -> Customer:
        customer = self.get_customer(customer_id)
        customer.is_active = not customer.is_active
        self.db.commit()
        self.db.refresh(customer)
        return self.get_customer(customer.id)

    def _get_category(self, category_id: int) -> CustomerCategory:
        category = self.repo.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户分类不存在或已删除")
        return category

    def _ensure_category_exists(self, category_id: int | None) -> None:
        if category_id is not None and self.repo.get_category(category_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="客户分类不存在或已删除")

    def _clear_default_categories(self, exclude_category_id: int | None = None) -> None:
        for category in self.repo.list_categories():
            if exclude_category_id is None or category.id != exclude_category_id:
                category.is_default = False
