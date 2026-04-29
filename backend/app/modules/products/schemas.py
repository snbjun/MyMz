from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class ProductMoneyQtyMixin(BaseModel):
    @field_serializer("sale_price", "purchase_price", "wholesale_price", check_fields=False)
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @field_serializer("stock_warning_qty", check_fields=False)
    def serialize_quantity(self, value: Decimal) -> str:
        return f"{value:.3f}"


class ProductCategoryRead(BaseModel):
    id: int
    name: str
    sort_order: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    sort_order: int = 0
    is_default: bool = False


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    sort_order: int | None = None
    is_default: bool | None = None


class ProductUnitRead(BaseModel):
    id: int
    name: str
    sort_order: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductUnitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    sort_order: int = 0
    is_default: bool = False


class ProductUnitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    sort_order: int | None = None
    is_default: bool | None = None


class ProductRead(ProductMoneyQtyMixin):
    id: int
    code: str | None = None
    barcode: str | None = None
    name: str
    category_id: int | None = None
    category_name: str | None = None
    unit_id: int | None = None
    unit_name: str | None = None
    spec: str | None = None
    model: str | None = None
    brand: str | None = None
    origin: str | None = None
    sale_price: Decimal
    purchase_price: Decimal
    wholesale_price: Decimal
    stock_warning_qty: Decimal
    image_url: str | None = None
    remark: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def fill_names(cls, value):
        if hasattr(value, "category") or hasattr(value, "unit"):
            return {
                "id": value.id,
                "code": value.code,
                "barcode": value.barcode,
                "name": value.name,
                "category_id": value.category_id,
                "category_name": value.category.name if value.category else None,
                "unit_id": value.unit_id,
                "unit_name": value.unit.name if value.unit else None,
                "spec": value.spec,
                "model": value.model,
                "brand": value.brand,
                "origin": value.origin,
                "sale_price": value.sale_price,
                "purchase_price": value.purchase_price,
                "wholesale_price": value.wholesale_price,
                "stock_warning_qty": value.stock_warning_qty,
                "image_url": value.image_url,
                "remark": value.remark,
                "is_active": value.is_active,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
        return value


class ProductListResponse(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int


class ProductBase(ProductMoneyQtyMixin):
    code: str | None = Field(default=None, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    category_id: int | None = None
    unit_id: int | None = None
    spec: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    brand: str | None = Field(default=None, max_length=128)
    origin: str | None = Field(default=None, max_length=128)
    sale_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    purchase_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    wholesale_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    stock_warning_qty: Decimal = Field(default=Decimal("0.000"), ge=Decimal("0.000"))
    image_url: str | None = Field(default=None, max_length=255)
    remark: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    category_id: int | None = None
    unit_id: int | None = None
    spec: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    brand: str | None = Field(default=None, max_length=128)
    origin: str | None = Field(default=None, max_length=128)
    sale_price: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    purchase_price: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    wholesale_price: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    stock_warning_qty: Decimal | None = Field(default=None, ge=Decimal("0.000"))
    image_url: str | None = Field(default=None, max_length=255)
    remark: str | None = None
    is_active: bool | None = None


class SuccessResponse(BaseModel):
    success: bool = True
