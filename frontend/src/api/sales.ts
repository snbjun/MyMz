import { http } from "@/api/http";
import type {
  SalesOrderDetail,
  SalesOrderListResponse,
  SalesOrderPayload,
  SalesPaymentPayload,
  SalesShipPayload,
} from "@/types/sales";

export interface SalesOrderListParams {
  keyword?: string;
  customer_id?: number;
  status?: string;
  delivery_status?: string;
  payment_status?: string;
  start_date?: string;
  end_date?: string;
  page: number;
  page_size: number;
}

export function listSalesOrders(params: SalesOrderListParams) {
  return http.get<SalesOrderListResponse>("/sales-orders", { params });
}

export function getSalesOrder(id: number) {
  return http.get<SalesOrderDetail>(`/sales-orders/${id}`);
}

export function createSalesOrder(payload: SalesOrderPayload) {
  return http.post<SalesOrderDetail>("/sales-orders", payload);
}

export function updateSalesOrder(id: number, payload: SalesOrderPayload) {
  return http.put<SalesOrderDetail>(`/sales-orders/${id}`, payload);
}

export function confirmSalesOrder(id: number) {
  return http.post<SalesOrderDetail>(`/sales-orders/${id}/confirm`);
}

export function shipSalesOrder(id: number, payload: SalesShipPayload) {
  return http.post<SalesOrderDetail>(`/sales-orders/${id}/ship`, payload);
}

export function createSalesPayment(id: number, payload: SalesPaymentPayload) {
  return http.post<SalesOrderDetail>(`/sales-orders/${id}/payments`, payload);
}

export function cancelSalesOrder(id: number, reason: string) {
  return http.post<SalesOrderDetail>(`/sales-orders/${id}/cancel`, { reason });
}
