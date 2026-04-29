from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.inventory.model import Warehouse
from app.modules.inventory.schemas import (
    InitialStockCreate,
    InventoryAdjustmentCreate,
    InventoryListResponse,
    InventoryRead,
    StockMovementListResponse,
    StockMovementRead,
    WarehouseRead,
)
from app.modules.inventory.service import InventoryService
from app.modules.users.model import User

router = APIRouter()


@router.get("/warehouses", response_model=list[WarehouseRead])
def list_warehouses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Warehouse]:
    return InventoryService(db).list_warehouses()


@router.get("/inventory", response_model=InventoryListResponse)
def list_inventory(
    keyword: str | None = None,
    category_id: int | None = None,
    warehouse_id: int | None = None,
    low_stock_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryListResponse:
    return InventoryService(db).list_inventory(keyword, category_id, warehouse_id, low_stock_only, page, page_size)


@router.post("/inventory/initial-stock", response_model=InventoryRead)
def set_initial_stock(
    payload: InitialStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryRead:
    return InventoryService(db).set_initial_stock(payload, current_user)


@router.post("/inventory/adjustments", response_model=InventoryRead)
def adjust_inventory(
    payload: InventoryAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryRead:
    return InventoryService(db).adjust_inventory(payload, current_user)


@router.get("/inventory/{product_id}", response_model=InventoryRead)
def get_inventory(
    product_id: int,
    warehouse_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryRead:
    return InventoryService(db).get_inventory(product_id, warehouse_id)


@router.get("/stock-movements", response_model=StockMovementListResponse)
def list_stock_movements(
    keyword: str | None = None,
    product_id: int | None = None,
    warehouse_id: int | None = None,
    movement_type: str | None = None,
    direction: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockMovementListResponse:
    return InventoryService(db).list_movements(
        keyword,
        product_id,
        warehouse_id,
        movement_type,
        direction,
        start_date,
        end_date,
        page,
        page_size,
    )


@router.get("/stock-movements/{movement_id}", response_model=StockMovementRead)
def get_stock_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockMovementRead:
    return InventoryService(db).get_movement(movement_id)
