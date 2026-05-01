import type { CurrentUser } from "@/api/auth";

export enum Permission {
  USERS_MANAGE = "users.manage",
  CUSTOMERS_MANAGE = "customers.manage",
  SUPPLIERS_MANAGE = "suppliers.manage",
  PRODUCTS_MANAGE = "products.manage",
  INVENTORY_MANAGE = "inventory.manage",
  SALES_MANAGE = "sales.manage",
  PURCHASE_MANAGE = "purchase.manage",
  FINANCE_MANAGE = "finance.manage",
  REPORTS_VIEW = "reports.view",
  PRINTING_MANAGE = "printing.manage",
  BACKUPS_MANAGE = "backups.manage",
  AUDIT_LOGS_VIEW = "audit_logs.view",
  SETTINGS_MANAGE = "settings.manage",
}

const staffPermissions = new Set<Permission>([
  Permission.CUSTOMERS_MANAGE,
  Permission.SUPPLIERS_MANAGE,
  Permission.PRODUCTS_MANAGE,
  Permission.INVENTORY_MANAGE,
  Permission.SALES_MANAGE,
  Permission.PURCHASE_MANAGE,
  Permission.FINANCE_MANAGE,
  Permission.REPORTS_VIEW,
  Permission.PRINTING_MANAGE,
]);

const rolePermissions: Record<string, Set<Permission>> = {
  admin: new Set(
    Object.values(Permission).filter((permission) => permission !== Permission.BACKUPS_MANAGE),
  ),
  staff: staffPermissions,
  viewer: new Set([Permission.REPORTS_VIEW]),
};

export function hasPermission(user: CurrentUser | null, permission: Permission) {
  if (!user || !user.is_active) {
    return false;
  }
  if (user.is_superuser) {
    return true;
  }
  return rolePermissions[user.role]?.has(permission) || false;
}

export function hasAnyPermission(user: CurrentUser | null, permissions: Permission[]) {
  return permissions.some((permission) => hasPermission(user, permission));
}
