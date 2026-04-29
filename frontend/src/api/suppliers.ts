import { http } from "@/api/http";
import type {
  SupplierCategory,
  SupplierListResponse,
  SupplierPayload,
  SupplierRecord,
} from "@/types/supplier";

export interface SupplierListParams {
  keyword?: string;
  category_id?: number;
  is_active?: boolean;
  page: number;
  page_size: number;
}

export function listSupplierCategories() {
  return http.get<SupplierCategory[]>("/supplier-categories");
}

export function createSupplierCategory(payload: { name: string; sort_order: number; is_default: boolean }) {
  return http.post<SupplierCategory>("/supplier-categories", payload);
}

export function updateSupplierCategory(
  id: number,
  payload: { name: string; sort_order: number; is_default: boolean },
) {
  return http.put<SupplierCategory>(`/supplier-categories/${id}`, payload);
}

export function deleteSupplierCategory(id: number) {
  return http.delete<{ success: boolean }>(`/supplier-categories/${id}`);
}

export function listSuppliers(params: SupplierListParams) {
  return http.get<SupplierListResponse>("/suppliers", { params });
}

export function getSupplier(id: number) {
  return http.get<SupplierRecord>(`/suppliers/${id}`);
}

export function createSupplier(payload: SupplierPayload) {
  return http.post<SupplierRecord>("/suppliers", payload);
}

export function updateSupplier(id: number, payload: SupplierPayload) {
  return http.put<SupplierRecord>(`/suppliers/${id}`, payload);
}

export function deleteSupplier(id: number) {
  return http.delete<{ success: boolean }>(`/suppliers/${id}`);
}

export function toggleSupplierActive(id: number) {
  return http.post<SupplierRecord>(`/suppliers/${id}/toggle-active`);
}

