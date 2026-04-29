import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import MainLayout from "@/layouts/MainLayout.vue";
import DashboardHome from "@/views/dashboard/DashboardHome.vue";
import LoginView from "@/views/login/LoginView.vue";
import PlaceholderView from "@/views/placeholder/PlaceholderView.vue";

export const moduleRoutes = [
  { path: "customers", name: "customers", titleKey: "customers" },
  { path: "suppliers", name: "suppliers", titleKey: "suppliers" },
  { path: "products", name: "products", titleKey: "products" },
  { path: "inventory", name: "inventory", titleKey: "inventory" },
  { path: "sales-orders", name: "salesOrders", titleKey: "salesOrders" },
  { path: "purchase-orders", name: "purchaseOrders", titleKey: "purchaseOrders" },
  { path: "expense-income", name: "expenseIncome", titleKey: "expenseIncome" },
  { path: "reports", name: "reports", titleKey: "reports" },
  { path: "users", name: "users", titleKey: "users" },
  { path: "settings", name: "settings", titleKey: "settings" },
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
        component: PlaceholderView,
        meta: { titleKey: route.titleKey },
      })),
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
