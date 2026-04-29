from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="staff", min_length=1, max_length=50)
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None
    is_superuser: bool | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class SuccessResponse(BaseModel):
    success: bool = True
