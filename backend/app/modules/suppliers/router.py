from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.permissions import Permission, require_permission
from app.modules.audit_logs.service import record_audit_log
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> SupplierCategory:
    category = SupplierService(db).create_category(payload)
    record_audit_log(db, current_user, "suppliers", "create_category", f"创建供应商分类：{category.name}", "supplier_category", category.id, category.name, request)
    return category


@router.put("/supplier-categories/{category_id}", response_model=SupplierCategoryRead)
def update_supplier_category(
    category_id: int,
    payload: SupplierCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> SupplierCategory:
    category = SupplierService(db).update_category(category_id, payload)
    record_audit_log(db, current_user, "suppliers", "update_category", f"编辑供应商分类：{category.name}", "supplier_category", category.id, category.name, request)
    return category


@router.delete("/supplier-categories/{category_id}", response_model=SuccessResponse)
def delete_supplier_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> SuccessResponse:
    SupplierService(db).delete_category(category_id)
    record_audit_log(db, current_user, "suppliers", "delete_category", f"删除供应商分类：{category_id}", "supplier_category", category_id, str(category_id), request)
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> Supplier:
    supplier = SupplierService(db).create_supplier(payload)
    record_audit_log(db, current_user, "suppliers", "create", f"创建供应商：{supplier.name}", "supplier", supplier.id, supplier.name, request)
    return supplier


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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> Supplier:
    supplier = SupplierService(db).update_supplier(supplier_id, payload)
    record_audit_log(db, current_user, "suppliers", "update", f"编辑供应商：{supplier.name}", "supplier", supplier.id, supplier.name, request)
    return supplier


@router.delete("/suppliers/{supplier_id}", response_model=SuccessResponse)
def delete_supplier(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> SuccessResponse:
    supplier = SupplierService(db).get_supplier(supplier_id)
    SupplierService(db).delete_supplier(supplier_id)
    record_audit_log(db, current_user, "suppliers", "delete", f"删除供应商：{supplier.name}", "supplier", supplier.id, supplier.name, request)
    return SuccessResponse()


@router.post("/suppliers/{supplier_id}/toggle-active", response_model=SupplierRead)
def toggle_supplier_active(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SUPPLIERS_MANAGE)),
) -> Supplier:
    supplier = SupplierService(db).toggle_active(supplier_id)
    record_audit_log(db, current_user, "suppliers", "toggle_active", f"启用禁用供应商：{supplier.name}", "supplier", supplier.id, supplier.name, request)
    return supplier

