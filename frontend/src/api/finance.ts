import { http } from "@/api/http";
import type {
  FinanceAccount,
  FinanceAccountPayload,
  FinanceCategory,
  FinanceCategoryPayload,
  FinanceRecord,
  FinanceRecordListResponse,
  FinanceRecordPayload,
  FinanceRecordStatus,
  FinanceType,
} from "@/types/finance";

export interface FinanceRecordListParams {
  keyword?: string;
  type?: FinanceType | "";
  category_id?: number;
  account_id?: number;
  status?: FinanceRecordStatus | "";
  start_date?: string;
  end_date?: string;
  page: number;
  page_size: number;
}

export function listFinanceCategories(params?: { type?: FinanceType; is_active?: boolean }) {
  return http.get<FinanceCategory[]>("/finance-categories", { params });
}

export function createFinanceCategory(payload: FinanceCategoryPayload) {
  return http.post<FinanceCategory>("/finance-categories", payload);
}

export function updateFinanceCategory(id: number, payload: Partial<FinanceCategoryPayload>) {
  return http.put<FinanceCategory>(`/finance-categories/${id}`, payload);
}

export function deleteFinanceCategory(id: number) {
  return http.delete<{ success: boolean }>(`/finance-categories/${id}`);
}

export function toggleFinanceCategoryActive(id: number) {
  return http.post<FinanceCategory>(`/finance-categories/${id}/toggle-active`);
}

export function listFinanceAccounts(params?: { is_active?: boolean }) {
  return http.get<FinanceAccount[]>("/finance-accounts", { params });
}

export function getFinanceAccount(id: number) {
  return http.get<FinanceAccount>(`/finance-accounts/${id}`);
}

export function createFinanceAccount(payload: FinanceAccountPayload) {
  return http.post<FinanceAccount>("/finance-accounts", payload);
}

export function updateFinanceAccount(id: number, payload: Partial<FinanceAccountPayload>) {
  return http.put<FinanceAccount>(`/finance-accounts/${id}`, payload);
}

export function deleteFinanceAccount(id: number) {
  return http.delete<{ success: boolean }>(`/finance-accounts/${id}`);
}

export function toggleFinanceAccountActive(id: number) {
  return http.post<FinanceAccount>(`/finance-accounts/${id}/toggle-active`);
}

export function listFinanceRecords(params: FinanceRecordListParams) {
  return http.get<FinanceRecordListResponse>("/finance-records", { params });
}

export function getFinanceRecord(id: number) {
  return http.get<FinanceRecord>(`/finance-records/${id}`);
}

export function createFinanceRecord(payload: FinanceRecordPayload) {
  return http.post<FinanceRecord>("/finance-records", payload);
}

export function voidFinanceRecord(id: number, reason: string) {
  return http.post<FinanceRecord>(`/finance-records/${id}/void`, { reason });
}
