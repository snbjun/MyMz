export type FinanceType = "income" | "expense";
export type FinanceRecordStatus = "normal" | "voided";
export type FinanceAccountType = "cash" | "bank" | "wechat" | "alipay" | "other";

export interface FinanceCategory {
  id: number;
  name: string;
  type: FinanceType;
  sort_order: number;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FinanceCategoryPayload {
  name: string;
  type: FinanceType;
  sort_order: number;
  is_default: boolean;
  is_active: boolean;
}

export interface FinanceAccount {
  id: number;
  name: string;
  type: FinanceAccountType;
  opening_balance: string;
  current_balance: string;
  sort_order: number;
  is_default: boolean;
  is_active: boolean;
  remark: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinanceAccountPayload {
  name: string;
  type: FinanceAccountType;
  opening_balance?: string;
  sort_order: number;
  is_default: boolean;
  is_active: boolean;
  remark?: string | null;
}

export interface FinanceRecord {
  id: number;
  record_no: string;
  type: FinanceType;
  record_date: string;
  category_id: number;
  category_name: string;
  account_id: number;
  account_name: string;
  amount: string;
  counterparty_type: string | null;
  counterparty_id: number | null;
  summary: string | null;
  remark: string | null;
  status: FinanceRecordStatus;
  created_by_id: number | null;
  created_by_name: string | null;
  voided_by_id: number | null;
  voided_at: string | null;
  void_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinanceRecordPayload {
  type: FinanceType;
  record_date: string;
  category_id: number;
  account_id: number;
  amount: string;
  summary?: string | null;
  remark?: string | null;
}

export interface FinanceRecordListResponse {
  items: FinanceRecord[];
  total: number;
  page: number;
  page_size: number;
}
