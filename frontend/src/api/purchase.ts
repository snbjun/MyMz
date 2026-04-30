import { http } from "@/api/http";
import type {
  PurchaseOrderDetail,
  PurchaseOrderListResponse,
  PurchaseOrderPayload,
  PurchasePaymentPayload,
  PurchaseReceivePayload,
} from "@/types/purchase";

export interface PurchaseOrderListParams {
  keyword?: string;
  supplier_id?: number;
  status?: string;
  receive_status?: string;
  payment_status?: string;
  start_date?: string;
  end_date?: string;
  page: number;
  page_size: number;
}

export function listPurchaseOrders(params: PurchaseOrderListParams) {
  return http.get<PurchaseOrderListResponse>("/purchase-orders", { params });
}

export function getPurchaseOrder(id: number) {
  return http.get<PurchaseOrderDetail>(`/purchase-orders/${id}`);
}

export function createPurchaseOrder(payload: PurchaseOrderPayload) {
  return http.post<PurchaseOrderDetail>("/purchase-orders", payload);
}

export function updatePurchaseOrder(id: number, payload: PurchaseOrderPayload) {
  return http.put<PurchaseOrderDetail>(`/purchase-orders/${id}`, payload);
}

export function confirmPurchaseOrder(id: number) {
  return http.post<PurchaseOrderDetail>(`/purchase-orders/${id}/confirm`);
}

export function receivePurchaseOrder(id: number, payload: PurchaseReceivePayload) {
  return http.post<PurchaseOrderDetail>(`/purchase-orders/${id}/receive`, payload);
}

export function createPurchasePayment(id: number, payload: PurchasePaymentPayload) {
  return http.post<PurchaseOrderDetail>(`/purchase-orders/${id}/payments`, payload);
}

export function cancelPurchaseOrder(id: number, reason: string) {
  return http.post<PurchaseOrderDetail>(`/purchase-orders/${id}/cancel`, { reason });
}
