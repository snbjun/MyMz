import { http } from "@/api/http";
import type {
  FinanceByCategoryItem,
  FinanceSummary,
  InventoryMovementSummary,
  InventorySummary,
  OverviewReport,
  PageResponse,
  PayableItem,
  ProfitSummary,
  PurchaseByProductItem,
  PurchaseBySupplierItem,
  PurchaseSummary,
  ReceivableItem,
  SalesByCustomerItem,
  SalesByProductItem,
  SalesSummary,
} from "@/types/report";

export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
}

export interface PageParams extends DateRangeParams {
  page: number;
  page_size: number;
}

export function getReportOverview(params?: DateRangeParams) {
  return http.get<OverviewReport>("/reports/overview", { params });
}

export function getSalesSummary(params?: DateRangeParams) {
  return http.get<SalesSummary>("/reports/sales/summary", { params });
}

export function getSalesByCustomer(params: PageParams) {
  return http.get<PageResponse<SalesByCustomerItem>>("/reports/sales/by-customer", { params });
}

export function getSalesByProduct(params: PageParams) {
  return http.get<PageResponse<SalesByProductItem>>("/reports/sales/by-product", { params });
}

export function getPurchaseSummary(params?: DateRangeParams) {
  return http.get<PurchaseSummary>("/reports/purchase/summary", { params });
}

export function getPurchaseBySupplier(params: PageParams) {
  return http.get<PageResponse<PurchaseBySupplierItem>>("/reports/purchase/by-supplier", { params });
}

export function getPurchaseByProduct(params: PageParams) {
  return http.get<PageResponse<PurchaseByProductItem>>("/reports/purchase/by-product", { params });
}

export function getReceivables(params: { keyword?: string; include_zero?: boolean; page: number; page_size: number }) {
  return http.get<PageResponse<ReceivableItem>>("/reports/receivables", { params });
}

export function getPayables(params: { keyword?: string; include_zero?: boolean; page: number; page_size: number }) {
  return http.get<PageResponse<PayableItem>>("/reports/payables", { params });
}

export function getInventorySummary() {
  return http.get<InventorySummary>("/reports/inventory/summary");
}

export function getInventoryMovementSummary(params?: DateRangeParams) {
  return http.get<InventoryMovementSummary>("/reports/inventory/movement-summary", { params });
}

export function getFinanceSummary(params?: DateRangeParams) {
  return http.get<FinanceSummary>("/reports/finance/summary", { params });
}

export function getFinanceByCategory(params: PageParams) {
  return http.get<PageResponse<FinanceByCategoryItem>>("/reports/finance/by-category", { params });
}

export function getProfitReport(params?: DateRangeParams) {
  return http.get<ProfitSummary>("/reports/profit", { params });
}
