from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.inventory.model import Inventory, StockMovement, Warehouse
from app.modules.products.model import Product, ProductCategory, ProductUnit
from app.modules.users.model import User


class InventoryRepository:
    """第 6 阶段新增：库存查询和库存行读写集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_warehouses(self) -> list[Warehouse]:
        stmt = (
            select(Warehouse)
            .where(Warehouse.deleted_at.is_(None), Warehouse.is_active.is_(True))
            .order_by(Warehouse.sort_order.asc(), Warehouse.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_default_warehouse(self) -> Warehouse | None:
        return self.db.scalar(
            select(Warehouse).where(
                Warehouse.deleted_at.is_(None),
                Warehouse.is_active.is_(True),
                Warehouse.is_default.is_(True),
            )
        )

    def get_warehouse(self, warehouse_id: int) -> Warehouse | None:
        return self.db.scalar(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.deleted_at.is_(None),
                Warehouse.is_active.is_(True),
            )
        )

    def get_product(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.unit))
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )
        return self.db.scalar(stmt)

    def get_inventory(self, product_id: int, warehouse_id: int) -> Inventory | None:
        return self.db.scalar(
            select(Inventory).where(Inventory.product_id == product_id, Inventory.warehouse_id == warehouse_id)
        )

    def get_or_create_inventory(self, product_id: int, warehouse_id: int) -> Inventory:
        inventory = self.get_inventory(product_id, warehouse_id)
        if inventory is not None:
            return inventory
        inventory = Inventory(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=Decimal("0.000"),
            average_cost=Decimal("0.0000"),
            total_cost=Decimal("0.00"),
        )
        self.db.add(inventory)
        self.db.flush()
        return inventory

    def count_movements_for_product_warehouse(self, product_id: int, warehouse_id: int) -> int:
        stmt = select(func.count()).select_from(StockMovement).where(
            StockMovement.product_id == product_id,
            StockMovement.warehouse_id == warehouse_id,
        )
        return int(self.db.scalar(stmt) or 0)

    def next_movement_no(self) -> str:
        prefix = f"KC{datetime.now():%Y%m%d}"
        stmt = (
            select(StockMovement.movement_no)
            .where(StockMovement.movement_no.like(f"{prefix}%"))
            .order_by(StockMovement.movement_no.desc())
            .limit(1)
        )
        last_no = self.db.scalar(stmt)
        next_seq = 1
        if last_no:
            next_seq = int(last_no[-4:]) + 1
        return f"{prefix}{next_seq:04d}"

    def create_movement(self, movement: StockMovement) -> StockMovement:
        self.db.add(movement)
        self.db.flush()
        return movement

    def list_inventory(
        self,
        warehouse: Warehouse,
        keyword: str | None,
        category_id: int | None,
        low_stock_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        qty = func.coalesce(Inventory.quantity_on_hand, Decimal("0.000"))
        avg_cost = func.coalesce(Inventory.average_cost, Decimal("0.0000"))
        total_cost = func.coalesce(Inventory.total_cost, Decimal("0.00"))
        updated_at = Inventory.updated_at
        filters = [Product.deleted_at.is_(None)]
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    Product.name.like(like_keyword),
                    Product.code.like(like_keyword),
                    Product.barcode.like(like_keyword),
                    Product.spec.like(like_keyword),
                    Product.model.like(like_keyword),
                    Product.brand.like(like_keyword),
                )
            )
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if low_stock_only:
            filters.append(Product.is_active.is_(True))
            filters.append(Product.stock_warning_qty > 0)
            filters.append(qty <= Product.stock_warning_qty)

        base = (
            select(
                Product.id.label("product_id"),
                Product.code.label("product_code"),
                Product.barcode,
                Product.name.label("product_name"),
                Product.category_id,
                ProductCategory.name.label("category_name"),
                Product.unit_id,
                ProductUnit.name.label("unit_name"),
                Product.spec,
                Product.model,
                Product.brand,
                qty.label("quantity_on_hand"),
                avg_cost.label("average_cost"),
                total_cost.label("total_cost"),
                Product.stock_warning_qty,
                updated_at.label("updated_at"),
            )
            .select_from(Product)
            .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
            .outerjoin(ProductUnit, Product.unit_id == ProductUnit.id)
            .outerjoin(
                Inventory,
                and_(Inventory.product_id == Product.id, Inventory.warehouse_id == warehouse.id),
            )
            .where(and_(*filters))
        )
        total = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        rows = self.db.execute(
            base.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).mappings()
        items = []
        for row in rows:
            item = dict(row)
            item["warehouse_id"] = warehouse.id
            item["warehouse_name"] = warehouse.name
            item["is_low_stock"] = (
                item["stock_warning_qty"] > Decimal("0.000")
                and item["quantity_on_hand"] <= item["stock_warning_qty"]
                and self._product_is_active(item["product_id"])
            )
            items.append(item)
        return items, total

    def get_inventory_detail(self, product: Product, warehouse: Warehouse) -> dict:
        inventory = self.get_inventory(product.id, warehouse.id)
        qty = inventory.quantity_on_hand if inventory else Decimal("0.000")
        avg_cost = inventory.average_cost if inventory else Decimal("0.0000")
        total_cost = inventory.total_cost if inventory else Decimal("0.00")
        return {
            "product_id": product.id,
            "product_code": product.code,
            "barcode": product.barcode,
            "product_name": product.name,
            "category_id": product.category_id,
            "category_name": product.category.name if product.category else None,
            "unit_id": product.unit_id,
            "unit_name": product.unit.name if product.unit else None,
            "spec": product.spec,
            "model": product.model,
            "brand": product.brand,
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "quantity_on_hand": qty,
            "average_cost": avg_cost,
            "total_cost": total_cost,
            "stock_warning_qty": product.stock_warning_qty,
            "is_low_stock": product.is_active and product.stock_warning_qty > 0 and qty <= product.stock_warning_qty,
            "updated_at": inventory.updated_at if inventory else None,
        }

    def get_movement(self, movement_id: int) -> StockMovement | None:
        stmt = (
            select(StockMovement)
            .options(
                joinedload(StockMovement.product),
                joinedload(StockMovement.warehouse),
                joinedload(StockMovement.created_by),
            )
            .where(StockMovement.id == movement_id)
        )
        return self.db.scalar(stmt)

    def list_movements(
        self,
        keyword: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        movement_type: str | None,
        direction: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[StockMovement], int]:
        filters = []
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    StockMovement.movement_no.like(like_keyword),
                    StockMovement.remark.like(like_keyword),
                    Product.name.like(like_keyword),
                    Product.code.like(like_keyword),
                    Product.barcode.like(like_keyword),
                )
            )
        if product_id is not None:
            filters.append(StockMovement.product_id == product_id)
        if warehouse_id is not None:
            filters.append(StockMovement.warehouse_id == warehouse_id)
        if movement_type:
            filters.append(StockMovement.movement_type == movement_type)
        if direction:
            filters.append(StockMovement.direction == direction)
        if start_date:
            filters.append(StockMovement.created_at >= datetime.combine(start_date, time.min))
        if end_date:
            filters.append(StockMovement.created_at <= datetime.combine(end_date, time.max))
        where_clause = and_(*filters) if filters else True
        count_stmt = (
            select(func.count())
            .select_from(StockMovement)
            .join(Product, StockMovement.product_id == Product.id)
            .where(where_clause)
        )
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = (
            select(StockMovement)
            .options(
                joinedload(StockMovement.product),
                joinedload(StockMovement.warehouse),
                joinedload(StockMovement.created_by),
            )
            .join(Product, StockMovement.product_id == Product.id)
            .where(where_clause)
            .order_by(StockMovement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def _product_is_active(self, product_id: int) -> bool:
        return bool(self.db.scalar(select(Product.is_active).where(Product.id == product_id)))
