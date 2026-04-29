from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class DecimalStringMixin(BaseModel):
    @field_serializer("opening_payable", "current_payable", "credit_limit", check_fields=False)
    def serialize_decimal(self, value: Decimal) -> str:
        return f"{value:.2f}"


class SupplierCategoryRead(BaseModel):
    id: int
    name: str
    sort_order: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    sort_order: int = 0
    is_default: bool = False


class SupplierCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    sort_order: int | None = None
    is_default: bool | None = None


class SupplierRead(DecimalStringMixin):
    id: int
    code: str | None = None
    name: str
    category_id: int | None = None
    category_name: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    backup_phone: str | None = None
    email: str | None = None
    wechat: str | None = None
    address: str | None = None
    tax_number: str | None = None
    opening_payable: Decimal
    current_payable: Decimal
    credit_limit: Decimal
    remark: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def fill_category_name(cls, value):
        if hasattr(value, "category"):
            data = {
                "id": value.id,
                "code": value.code,
                "name": value.name,
                "category_id": value.category_id,
                "category_name": value.category.name if value.category else None,
                "contact_name": value.contact_name,
                "phone": value.phone,
                "backup_phone": value.backup_phone,
                "email": value.email,
                "wechat": value.wechat,
                "address": value.address,
                "tax_number": value.tax_number,
                "opening_payable": value.opening_payable,
                "current_payable": value.current_payable,
                "credit_limit": value.credit_limit,
                "remark": value.remark,
                "is_active": value.is_active,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
            return data
        return value


class SupplierListResponse(BaseModel):
    items: list[SupplierRead]
    total: int
    page: int
    page_size: int


class SupplierBase(DecimalStringMixin):
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    category_id: int | None = None
    contact_name: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    backup_phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    wechat: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=255)
    tax_number: str | None = Field(default=None, max_length=64)
    opening_payable: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    current_payable: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    remark: str | None = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    category_id: int | None = None
    contact_name: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    backup_phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    wechat: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=255)
    tax_number: str | None = Field(default=None, max_length=64)
    opening_payable: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    current_payable: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    credit_limit: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    remark: str | None = None
    is_active: bool | None = None


class SuccessResponse(BaseModel):
    success: bool = True

