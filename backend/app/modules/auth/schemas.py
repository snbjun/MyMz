from pydantic import BaseModel, Field

from app.modules.users.schemas import UserRead


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LogoutResponse(BaseModel):
    success: bool = True
