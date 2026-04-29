import { http } from "@/api/http";
import type {
  CustomerCategory,
  CustomerListResponse,
  CustomerPayload,
  CustomerRecord,
} from "@/types/customer";

export interface CustomerListParams {
  keyword?: string;
  category_id?: number;
  is_active?: boolean;
  page: number;
  page_size: number;
}

export function listCustomerCategories() {
  return http.get<CustomerCategory[]>("/customer-categories");
}

export function createCustomerCategory(payload: { name: string; sort_order: number; is_default: boolean }) {
  return http.post<CustomerCategory>("/customer-categories", payload);
}

export function updateCustomerCategory(
  id: number,
  payload: { name: string; sort_order: number; is_default: boolean },
) {
  return http.put<CustomerCategory>(`/customer-categories/${id}`, payload);
}

export function deleteCustomerCategory(id: number) {
  return http.delete<{ success: boolean }>(`/customer-categories/${id}`);
}

export function listCustomers(params: CustomerListParams) {
  return http.get<CustomerListResponse>("/customers", { params });
}

export function getCustomer(id: number) {
  return http.get<CustomerRecord>(`/customers/${id}`);
}

export function createCustomer(payload: CustomerPayload) {
  return http.post<CustomerRecord>("/customers", payload);
}

export function updateCustomer(id: number, payload: CustomerPayload) {
  return http.put<CustomerRecord>(`/customers/${id}`, payload);
}

export function deleteCustomer(id: number) {
  return http.delete<{ success: boolean }>(`/customers/${id}`);
}

export function toggleCustomerActive(id: number) {
  return http.post<CustomerRecord>(`/customers/${id}/toggle-active`);
}
