from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductCategory:
    return ProductService(db).create_category(payload)


@router.put("/product-categories/{category_id}", response_model=ProductCategoryRead)
def update_product_category(
    category_id: int,
    payload: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductCategory:
    return ProductService(db).update_category(category_id, payload)


@router.delete("/product-categories/{category_id}", response_model=SuccessResponse)
def delete_product_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    ProductService(db).delete_category(category_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductUnit:
    return ProductService(db).create_unit(payload)


@router.put("/product-units/{unit_id}", response_model=ProductUnitRead)
def update_product_unit(
    unit_id: int,
    payload: ProductUnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductUnit:
    return ProductService(db).update_unit(unit_id, payload)


@router.delete("/product-units/{unit_id}", response_model=SuccessResponse)
def delete_product_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    ProductService(db).delete_unit(unit_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Product:
    return ProductService(db).create_product(payload)


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Product:
    return ProductService(db).update_product(product_id, payload)


@router.delete("/products/{product_id}", response_model=SuccessResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    ProductService(db).delete_product(product_id)
    return SuccessResponse()


@router.post("/products/{product_id}/toggle-active", response_model=ProductRead)
def toggle_product_active(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Product:
    return ProductService(db).toggle_active(product_id)
