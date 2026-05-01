from collections.abc import Iterable
from enum import StrEnum

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.modules.users.model import User


class Permission(StrEnum):
    """第 13 阶段新增：轻量角色权限常量，保留 users.role 字段。"""

    USERS_MANAGE = "users.manage"
    CUSTOMERS_MANAGE = "customers.manage"
    SUPPLIERS_MANAGE = "suppliers.manage"
    PRODUCTS_MANAGE = "products.manage"
    INVENTORY_MANAGE = "inventory.manage"
    SALES_MANAGE = "sales.manage"
    PURCHASE_MANAGE = "purchase.manage"
    FINANCE_MANAGE = "finance.manage"
    REPORTS_VIEW = "reports.view"
    PRINTING_MANAGE = "printing.manage"
    BACKUPS_MANAGE = "backups.manage"
    AUDIT_LOGS_VIEW = "audit_logs.view"
    SETTINGS_MANAGE = "settings.manage"


STAFF_PERMISSIONS = {
    Permission.CUSTOMERS_MANAGE,
    Permission.SUPPLIERS_MANAGE,
    Permission.PRODUCTS_MANAGE,
    Permission.INVENTORY_MANAGE,
    Permission.SALES_MANAGE,
    Permission.PURCHASE_MANAGE,
    Permission.FINANCE_MANAGE,
    Permission.REPORTS_VIEW,
    Permission.PRINTING_MANAGE,
}

ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": {
        Permission.USERS_MANAGE,
        Permission.CUSTOMERS_MANAGE,
        Permission.SUPPLIERS_MANAGE,
        Permission.PRODUCTS_MANAGE,
        Permission.INVENTORY_MANAGE,
        Permission.SALES_MANAGE,
        Permission.PURCHASE_MANAGE,
        Permission.FINANCE_MANAGE,
        Permission.REPORTS_VIEW,
        Permission.PRINTING_MANAGE,
        Permission.AUDIT_LOGS_VIEW,
        Permission.SETTINGS_MANAGE,
    },
    "staff": STAFF_PERMISSIONS,
    "viewer": {Permission.REPORTS_VIEW},
}


def has_permission(user: User, permission: Permission | str) -> bool:
    if user.is_superuser:
        return True
    try:
        permission_value = Permission(permission)
    except ValueError:
        return False
    return permission_value in ROLE_PERMISSIONS.get(user.role, set())


def require_permission(permission: Permission | str):
    """第 13 阶段新增：业务接口使用的权限依赖。"""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权执行该操作")
        return current_user

    return dependency


def require_any_permission(permissions: Iterable[Permission | str]):
    permission_list = list(permissions)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not any(has_permission(current_user, permission) for permission in permission_list):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权执行该操作")
        return current_user

    return dependency
