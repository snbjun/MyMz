from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.customers.router import router as customers_router
from app.modules.products.router import router as products_router
from app.modules.suppliers.router import router as suppliers_router
from app.modules.users.router import router as users_router

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """骨架阶段新增：供本地开发、Docker 和测试使用的健康检查。"""

    return {"status": "ok", "service": "mymz-backend"}


router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(customers_router, tags=["customers"])
router.include_router(products_router, tags=["products"])
router.include_router(suppliers_router, tags=["suppliers"])
router.include_router(users_router, prefix="/users", tags=["users"])
