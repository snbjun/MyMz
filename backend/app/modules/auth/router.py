from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.modules.auth.schemas import LoginRequest, LoginResponse, LogoutResponse
from app.modules.auth.service import AuthService
from app.modules.users.model import User
from app.modules.users.schemas import UserRead

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return AuthService(db).login(payload)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: User = Depends(get_current_user)) -> LogoutResponse:
    return LogoutResponse()
