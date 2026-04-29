from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.customers.model import Customer, CustomerCategory
from app.modules.customers.schemas import (
    CustomerCategoryCreate,
    CustomerCategoryRead,
    CustomerCategoryUpdate,
    CustomerCreate,
    CustomerListResponse,
    CustomerRead,
    CustomerUpdate,
    SuccessResponse,
)
from app.modules.customers.service import CustomerService
from app.modules.users.model import User

router = APIRouter()


@router.get("/customer-categories", response_model=list[CustomerCategoryRead])
def list_customer_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CustomerCategory]:
    return CustomerService(db).list_categories()


@router.post("/customer-categories", response_model=CustomerCategoryRead)
def create_customer_category(
    payload: CustomerCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerCategory:
    return CustomerService(db).create_category(payload)


@router.put("/customer-categories/{category_id}", response_model=CustomerCategoryRead)
def update_customer_category(
    category_id: int,
    payload: CustomerCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerCategory:
    return CustomerService(db).update_category(category_id, payload)


@router.delete("/customer-categories/{category_id}", response_model=SuccessResponse)
def delete_customer_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    CustomerService(db).delete_category(category_id)
    return SuccessResponse()


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    keyword: str | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerListResponse:
    return CustomerService(db).list_customers(keyword, category_id, is_active, page, page_size)


@router.post("/customers", response_model=CustomerRead)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    return CustomerService(db).create_customer(payload)


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    return CustomerService(db).get_customer(customer_id)


@router.put("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    return CustomerService(db).update_customer(customer_id, payload)


@router.delete("/customers/{customer_id}", response_model=SuccessResponse)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    CustomerService(db).delete_customer(customer_id)
    return SuccessResponse()


@router.post("/customers/{customer_id}/toggle-active", response_model=CustomerRead)
def toggle_customer_active(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    return CustomerService(db).toggle_active(customer_id)
