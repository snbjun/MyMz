import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import MainLayout from "@/layouts/MainLayout.vue";
import { useAuthStore } from "@/stores/auth";
import { hasPermission, Permission } from "@/utils/permissions";
import AuditLogListView from "@/views/auditLogs/AuditLogListView.vue";
import CustomerManagementView from "@/views/customers/CustomerManagementView.vue";
import DashboardHome from "@/views/dashboard/DashboardHome.vue";
import FinanceManagementView from "@/views/finance/FinanceManagementView.vue";
import InventoryManagementView from "@/views/inventory/InventoryManagementView.vue";
import LoginView from "@/views/login/LoginView.vue";
import PlaceholderView from "@/views/placeholder/PlaceholderView.vue";
import ProductManagementView from "@/views/products/ProductManagementView.vue";
import PurchaseOrderPrintView from "@/views/printing/PurchaseOrderPrintView.vue";
import SalesOrderPrintView from "@/views/printing/SalesOrderPrintView.vue";
import PurchaseOrderListView from "@/views/purchase/PurchaseOrderListView.vue";
import ReportsView from "@/views/reports/ReportsView.vue";
import SalesOrderListView from "@/views/sales/SalesOrderListView.vue";
import BackupManagementView from "@/views/settings/BackupManagementView.vue";
import SupplierManagementView from "@/views/suppliers/SupplierManagementView.vue";
import UserManagementView from "@/views/users/UserManagementView.vue";

export const moduleRoutes = [
  { path: "customers", name: "customers", titleKey: "customers" },
  { path: "suppliers", name: "suppliers", titleKey: "suppliers" },
  { path: "products", name: "products", titleKey: "products" },
  { path: "inventory", name: "inventory", titleKey: "inventory" },
  { path: "sales-orders", name: "salesOrders", titleKey: "salesOrders" },
  { path: "purchase-orders", name: "purchaseOrders", titleKey: "purchaseOrders" },
  { path: "finance", name: "finance", titleKey: "expenseIncome" },
  { path: "reports", name: "reports", titleKey: "reports", permission: Permission.REPORTS_VIEW },
  { path: "users", name: "users", titleKey: "users", requiresSuperuser: true },
  { path: "audit-logs", name: "auditLogs", titleKey: "auditLogs", permission: Permission.AUDIT_LOGS_VIEW },
  { path: "settings/backups", name: "settings", titleKey: "settings", requiresSuperuser: true },
] as const;

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
  },
  {
    path: "/",
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "dashboard",
        component: DashboardHome,
        meta: { titleKey: "dashboard" },
      },
      ...moduleRoutes.map((route) => ({
        path: route.path,
        name: route.name,
        component:
          route.name === "users"
            ? UserManagementView
            : route.name === "customers"
              ? CustomerManagementView
              : route.name === "suppliers"
                ? SupplierManagementView
                : route.name === "products"
                  ? ProductManagementView
                  : route.name === "inventory"
                    ? InventoryManagementView
                    : route.name === "salesOrders"
                      ? SalesOrderListView
                      : route.name === "purchaseOrders"
                        ? PurchaseOrderListView
                        : route.name === "finance"
                          ? FinanceManagementView
                          : route.name === "reports"
                            ? ReportsView
                            : route.name === "auditLogs"
                              ? AuditLogListView
                            : route.name === "settings"
                              ? BackupManagementView
                          : PlaceholderView,
        meta: {
          titleKey: route.titleKey,
          requiresSuperuser: "requiresSuperuser" in route ? route.requiresSuperuser : false,
          permission: "permission" in route ? route.permission : undefined,
        },
      })),
    ],
  },
  {
    path: "/sales-orders/:id/print",
    name: "salesOrderPrint",
    component: SalesOrderPrintView,
    meta: { requiresAuth: true },
  },
  {
    path: "/purchase-orders/:id/print",
    name: "purchaseOrderPrint",
    component: PurchaseOrderPrintView,
    meta: { requiresAuth: true },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  if (to.name === "login") {
    if (authStore.isAuthenticated || (await authStore.restore())) {
      return { name: "dashboard" };
    }
    return true;
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    const restored = await authStore.restore();
    if (!restored) {
      return { name: "login", query: { redirect: to.fullPath } };
    }
  }

  if (to.meta.requiresSuperuser && !authStore.user?.is_superuser) {
    return { name: "dashboard", query: { forbidden: "1" } };
  }

  if (to.meta.permission && !hasPermission(authStore.user, to.meta.permission as Permission)) {
    return { name: "dashboard", query: { forbidden: "1" } };
  }

  return true;
});
