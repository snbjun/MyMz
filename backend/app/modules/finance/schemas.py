from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


FinanceType = Literal["income", "expense"]
AccountType = Literal["cash", "bank", "wechat", "alipay", "other"]
RecordStatus = Literal["normal", "voided"]


class FinanceDecimalMixin(BaseModel):
    @field_serializer("opening_balance", "current_balance", "amount", check_fields=False)
    def serialize_money(self, value: Decimal) -> str:
        return f"{value:.2f}"


class FinanceCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: FinanceType
    sort_order: int = 0
    is_default: bool = False
    is_active: bool = True


class FinanceCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    type: FinanceType | None = None
    sort_order: int | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class FinanceCategoryRead(BaseModel):
    id: int
    name: str
    type: str
    sort_order: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinanceAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: AccountType = "cash"
    opening_balance: Decimal = Decimal("0.00")
    sort_order: int = 0
    is_default: bool = False
    is_active: bool = True
    remark: str | None = None


class FinanceAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    type: AccountType | None = None
    opening_balance: Decimal | None = None
    sort_order: int | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    remark: str | None = None


class FinanceAccountRead(FinanceDecimalMixin):
    id: int
    name: str
    type: str
    opening_balance: Decimal
    current_balance: Decimal
    sort_order: int
    is_default: bool
    is_active: bool
    remark: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinanceRecordCreate(BaseModel):
    type: FinanceType
    record_date: date = Field(default_factory=date.today)
    category_id: int
    account_id: int
    amount: Decimal = Field(gt=0)
    counterparty_type: Literal["customer", "supplier", "other"] | None = None
    counterparty_id: int | None = None
    summary: str | None = Field(default=None, max_length=255)
    remark: str | None = None


class FinanceRecordVoid(BaseModel):
    reason: str = Field(min_length=1)


class FinanceRecordRead(FinanceDecimalMixin):
    id: int
    record_no: str
    type: str
    record_date: date
    category_id: int
    category_name: str
    account_id: int
    account_name: str
    amount: Decimal
    counterparty_type: str | None = None
    counterparty_id: int | None = None
    summary: str | None = None
    remark: str | None = None
    status: str
    created_by_id: int | None = None
    created_by_name: str | None = None
    voided_by_id: int | None = None
    voided_at: datetime | None = None
    void_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def fill_names(cls, value):
        if hasattr(value, "category"):
            return {
                "id": value.id,
                "record_no": value.record_no,
                "type": value.type,
                "record_date": value.record_date,
                "category_id": value.category_id,
                "category_name": value.category.name if value.category else "",
                "account_id": value.account_id,
                "account_name": value.account.name if value.account else "",
                "amount": value.amount,
                "counterparty_type": value.counterparty_type,
                "counterparty_id": value.counterparty_id,
                "summary": value.summary,
                "remark": value.remark,
                "status": value.status,
                "created_by_id": value.created_by_id,
                "created_by_name": value.created_by.display_name if value.created_by else None,
                "voided_by_id": value.voided_by_id,
                "voided_at": value.voided_at,
                "void_reason": value.void_reason,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
        return value

    model_config = ConfigDict(from_attributes=True)


class FinanceRecordListResponse(BaseModel):
    items: list[FinanceRecordRead]
    total: int
    page: int
    page_size: int


class SuccessResponse(BaseModel):
    success: bool = True
