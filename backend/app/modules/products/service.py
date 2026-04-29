from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.products.model import Product, ProductCategory, ProductUnit
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductUnitCreate,
    ProductUnitUpdate,
    ProductUpdate,
)


class ProductService:
    """第 5 阶段新增：产品档案业务规则，不处理库存。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    def list_categories(self) -> list[ProductCategory]:
        return self.repo.list_categories()

    def create_category(self, payload: ProductCategoryCreate) -> ProductCategory:
        if self.repo.get_category_by_name(payload.name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品分类名称已存在")
        if payload.is_default:
            self._clear_default_categories()
        category = ProductCategory(name=payload.name, sort_order=payload.sort_order, is_default=payload.is_default)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category_id: int, payload: ProductCategoryUpdate) -> ProductCategory:
        category = self._get_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and self.repo.has_other_category_with_name(data["name"], category_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品分类名称已存在")
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
        if self.repo.count_products_by_category(category_id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类正在被产品使用，不能删除")
        self.repo.soft_delete_category(category)
        self.db.commit()

    def list_units(self) -> list[ProductUnit]:
        return self.repo.list_units()

    def create_unit(self, payload: ProductUnitCreate) -> ProductUnit:
        if self.repo.get_unit_by_name(payload.name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品单位名称已存在")
        if payload.is_default:
            self._clear_default_units()
        unit = ProductUnit(name=payload.name, sort_order=payload.sort_order, is_default=payload.is_default)
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def update_unit(self, unit_id: int, payload: ProductUnitUpdate) -> ProductUnit:
        unit = self._get_unit(unit_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and self.repo.has_other_unit_with_name(data["name"], unit_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品单位名称已存在")
        if data.get("is_default") is True:
            self._clear_default_units(exclude_unit_id=unit_id)
        if unit.is_default and data.get("is_default") is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消默认单位")
        for field, value in data.items():
            setattr(unit, field, value)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def delete_unit(self, unit_id: int) -> None:
        unit = self._get_unit(unit_id)
        if unit.is_default or self.repo.count_active_units(exclude_unit_id=unit_id) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除默认单位")
        if self.repo.count_products_by_unit(unit_id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="单位正在被产品使用，不能删除")
        self.repo.soft_delete_unit(unit)
        self.db.commit()

    def list_products(
        self,
        keyword: str | None,
        category_id: int | None,
        unit_id: int | None,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> ProductListResponse:
        items, total = self.repo.list_products(keyword, category_id, unit_id, is_active, page, page_size)
        return ProductListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_product(self, product_id: int) -> Product:
        product = self.repo.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在或已删除")
        return product

    def create_product(self, payload: ProductCreate) -> Product:
        self._ensure_unique_product(payload.name, payload.code, payload.barcode)
        self._ensure_category_exists(payload.category_id)
        self._ensure_unit_exists(payload.unit_id)
        product = Product(**payload.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return self.get_product(product.id)

    def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] and self.repo.has_other_product_with_name(data["name"], product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品名称已存在")
        if "code" in data and data["code"] and self.repo.has_other_product_with_code(data["code"], product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品编号已存在")
        if "barcode" in data and data["barcode"] and self.repo.has_other_product_with_barcode(data["barcode"], product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品条码已存在")
        if "category_id" in data:
            self._ensure_category_exists(data["category_id"])
        if "unit_id" in data:
            self._ensure_unit_exists(data["unit_id"])
        for numeric_field in ("sale_price", "purchase_price", "wholesale_price", "stock_warning_qty"):
            if numeric_field in data and data[numeric_field] is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="金额或数量字段不能为空")
        for field, value in data.items():
            setattr(product, field, value)
        self.db.commit()
        self.db.refresh(product)
        return self.get_product(product.id)

    def delete_product(self, product_id: int) -> None:
        product = self.get_product(product_id)
        self.repo.soft_delete_product(product)
        self.db.commit()

    def toggle_active(self, product_id: int) -> Product:
        product = self.get_product(product_id)
        product.is_active = not product.is_active
        self.db.commit()
        self.db.refresh(product)
        return self.get_product(product.id)

    def _ensure_unique_product(self, name: str, code: str | None, barcode: str | None) -> None:
        if self.repo.get_product_by_name(name) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品名称已存在")
        if code and self.repo.get_product_by_code(code) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品编号已存在")
        if barcode and self.repo.get_product_by_barcode(barcode) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品条码已存在")

    def _get_category(self, category_id: int) -> ProductCategory:
        category = self.repo.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品分类不存在或已删除")
        return category

    def _get_unit(self, unit_id: int) -> ProductUnit:
        unit = self.repo.get_unit(unit_id)
        if unit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品单位不存在或已删除")
        return unit

    def _ensure_category_exists(self, category_id: int | None) -> None:
        if category_id is not None and self.repo.get_category(category_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品分类不存在或已删除")

    def _ensure_unit_exists(self, unit_id: int | None) -> None:
        if unit_id is not None and self.repo.get_unit(unit_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品单位不存在或已删除")

    def _clear_default_categories(self, exclude_category_id: int | None = None) -> None:
        for category in self.repo.list_categories():
            if exclude_category_id is None or category.id != exclude_category_id:
                category.is_default = False

    def _clear_default_units(self, exclude_unit_id: int | None = None) -> None:
        for unit in self.repo.list_units():
            if exclude_unit_id is None or unit.id != exclude_unit_id:
                unit.is_default = False
