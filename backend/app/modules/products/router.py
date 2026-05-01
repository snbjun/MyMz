from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.permissions import Permission, require_permission
from app.modules.audit_logs.service import record_audit_log
from app.modules.products.model import Product, ProductCategory, ProductUnit
from app.modules.products.schemas import (
    ProductCategoryCreate,
    ProductCategoryRead,
    ProductCategoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductRead,
    ProductUnitCreate,
    ProductUnitRead,
    ProductUnitUpdate,
    ProductUpdate,
    SuccessResponse,
)
from app.modules.products.service import ProductService
from app.modules.users.model import User

router = APIRouter()


@router.get("/product-categories", response_model=list[ProductCategoryRead])
def list_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProductCategory]:
    return ProductService(db).list_categories()


@router.post("/product-categories", response_model=ProductCategoryRead)
def create_product_category(
    payload: ProductCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> ProductCategory:
    category = ProductService(db).create_category(payload)
    record_audit_log(db, current_user, "products", "create_category", f"创建产品分类：{category.name}", "product_category", category.id, category.name, request)
    return category


@router.put("/product-categories/{category_id}", response_model=ProductCategoryRead)
def update_product_category(
    category_id: int,
    payload: ProductCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> ProductCategory:
    category = ProductService(db).update_category(category_id, payload)
    record_audit_log(db, current_user, "products", "update_category", f"编辑产品分类：{category.name}", "product_category", category.id, category.name, request)
    return category


@router.delete("/product-categories/{category_id}", response_model=SuccessResponse)
def delete_product_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> SuccessResponse:
    ProductService(db).delete_category(category_id)
    record_audit_log(db, current_user, "products", "delete_category", f"删除产品分类：{category_id}", "product_category", category_id, str(category_id), request)
    return SuccessResponse()


@router.get("/product-units", response_model=list[ProductUnitRead])
def list_product_units(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProductUnit]:
    return ProductService(db).list_units()


@router.post("/product-units", response_model=ProductUnitRead)
def create_product_unit(
    payload: ProductUnitCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> ProductUnit:
    unit = ProductService(db).create_unit(payload)
    record_audit_log(db, current_user, "products", "create_unit", f"创建产品单位：{unit.name}", "product_unit", unit.id, unit.name, request)
    return unit


@router.put("/product-units/{unit_id}", response_model=ProductUnitRead)
def update_product_unit(
    unit_id: int,
    payload: ProductUnitUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> ProductUnit:
    unit = ProductService(db).update_unit(unit_id, payload)
    record_audit_log(db, current_user, "products", "update_unit", f"编辑产品单位：{unit.name}", "product_unit", unit.id, unit.name, request)
    return unit


@router.delete("/product-units/{unit_id}", response_model=SuccessResponse)
def delete_product_unit(
    unit_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> SuccessResponse:
    ProductService(db).delete_unit(unit_id)
    record_audit_log(db, current_user, "products", "delete_unit", f"删除产品单位：{unit_id}", "product_unit", unit_id, str(unit_id), request)
    return SuccessResponse()


@router.get("/products", response_model=ProductListResponse)
def list_products(
    keyword: str | None = None,
    category_id: int | None = None,
    unit_id: int | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductListResponse:
    return ProductService(db).list_products(keyword, category_id, unit_id, is_active, page, page_size)


@router.post("/products", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> Product:
    product = ProductService(db).create_product(payload)
    record_audit_log(db, current_user, "products", "create", f"创建产品：{product.name}", "product", product.id, product.name, request)
    return product


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Product:
    return ProductService(db).get_product(product_id)


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> Product:
    product = ProductService(db).update_product(product_id, payload)
    record_audit_log(db, current_user, "products", "update", f"编辑产品：{product.name}", "product", product.id, product.name, request)
    return product


@router.delete("/products/{product_id}", response_model=SuccessResponse)
def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> SuccessResponse:
    product = ProductService(db).get_product(product_id)
    ProductService(db).delete_product(product_id)
    record_audit_log(db, current_user, "products", "delete", f"删除产品：{product.name}", "product", product.id, product.name, request)
    return SuccessResponse()


@router.post("/products/{product_id}/toggle-active", response_model=ProductRead)
def toggle_product_active(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCTS_MANAGE)),
) -> Product:
    product = ProductService(db).toggle_active(product_id)
    record_audit_log(db, current_user, "products", "toggle_active", f"启用禁用产品：{product.name}", "product", product.id, product.name, request)
    return product
