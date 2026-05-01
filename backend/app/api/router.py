from fastapi import APIRouter

from app.modules.audit_logs.router import router as audit_logs_router
from app.modules.auth.router import router as auth_router
from app.modules.backups.router import router as backups_router
from app.modules.customers.router import router as customers_router
from app.modules.finance.router import router as finance_router
from app.modules.inventory.router import router as inventory_router
from app.modules.print_templates.router import router as print_templates_router
from app.modules.products.router import router as products_router
from app.modules.purchase.router import router as purchase_router
from app.modules.reports.router import router as reports_router
from app.modules.sales.router import router as sales_router
from app.modules.suppliers.router import router as suppliers_router
from app.modules.users.router import router as users_router

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """骨架阶段新增：供本地开发、Docker 和测试使用的健康检查。"""

    return {"status": "ok", "service": "mymz-backend"}


router.include_router(audit_logs_router, tags=["audit_logs"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(backups_router, tags=["backups"])
router.include_router(customers_router, tags=["customers"])
router.include_router(finance_router, tags=["finance"])
router.include_router(inventory_router, tags=["inventory"])
router.include_router(print_templates_router, tags=["print"])
router.include_router(products_router, tags=["products"])
router.include_router(purchase_router, tags=["purchase"])
router.include_router(reports_router, tags=["reports"])
router.include_router(sales_router, tags=["sales"])
router.include_router(suppliers_router, tags=["suppliers"])
router.include_router(users_router, prefix="/users", tags=["users"])
