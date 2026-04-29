export interface CustomerCategory {
  id: number;
  name: string;
  sort_order: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerRecord {
  id: number;
  code: string | null;
  name: string;
  category_id: number | null;
  category_name: string | null;
  contact_name: string | null;
  phone: string | null;
  backup_phone: string | null;
  email: string | null;
  wechat: string | null;
  address: string | null;
  tax_number: string | null;
  opening_receivable: string;
  current_receivable: string;
  credit_limit: string;
  remark: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerListResponse {
  items: CustomerRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface CustomerPayload {
  code?: string | null;
  name: string;
  category_id?: number | null;
  contact_name?: string | null;
  phone?: string | null;
  backup_phone?: string | null;
  email?: string | null;
  wechat?: string | null;
  address?: string | null;
  tax_number?: string | null;
  opening_receivable: string;
  current_receivable: string;
  credit_limit: string;
  remark?: string | null;
  is_active: boolean;
}
