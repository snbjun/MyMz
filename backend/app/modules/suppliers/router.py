from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.suppliers.model import Supplier, SupplierCategory
from app.modules.suppliers.schemas import (
    SupplierCategoryCreate,
    SupplierCategoryRead,
    SupplierCategoryUpdate,
    SupplierCreate,
    SupplierListResponse,
    SupplierRead,
    SupplierUpdate,
    SuccessResponse,
)
from app.modules.suppliers.service import SupplierService
from app.modules.users.model import User

router = APIRouter()


@router.get("/supplier-categories", response_model=list[SupplierCategoryRead])
def list_supplier_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SupplierCategory]:
    return SupplierService(db).list_categories()


@router.post("/supplier-categories", response_model=SupplierCategoryRead)
def create_supplier_category(
    payload: SupplierCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupplierCategory:
    return SupplierService(db).create_category(payload)


@router.put("/supplier-categories/{category_id}", response_model=SupplierCategoryRead)
def update_supplier_category(
    category_id: int,
    payload: SupplierCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupplierCategory:
    return SupplierService(db).update_category(category_id, payload)


@router.delete("/supplier-categories/{category_id}", response_model=SuccessResponse)
def delete_supplier_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    SupplierService(db).delete_category(category_id)
    return SuccessResponse()


@router.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers(
    keyword: str | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupplierListResponse:
    return SupplierService(db).list_suppliers(keyword, category_id, is_active, page, page_size)


@router.post("/suppliers", response_model=SupplierRead)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Supplier:
    return SupplierService(db).create_supplier(payload)


@router.get("/suppliers/{supplier_id}", response_model=SupplierRead)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Supplier:
    return SupplierService(db).get_supplier(supplier_id)


@router.put("/suppliers/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Supplier:
    return SupplierService(db).update_supplier(supplier_id, payload)


@router.delete("/suppliers/{supplier_id}", response_model=SuccessResponse)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    SupplierService(db).delete_supplier(supplier_id)
    return SuccessResponse()


@router.post("/suppliers/{supplier_id}/toggle-active", response_model=SupplierRead)
def toggle_supplier_active(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Supplier:
    return SupplierService(db).toggle_active(supplier_id)

