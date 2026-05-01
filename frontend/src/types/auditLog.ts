export interface AuditLogRecord {
  id: number;
  user_id: number | null;
  username: string | null;
  module: string;
  action: string;
  target_type: string | null;
  target_id: number | null;
  target_label: string | null;
  method: string | null;
  path: string | null;
  ip_address: string | null;
  user_agent: string | null;
  summary: string;
  created_at: string;
}

export interface AuditLogListParams {
  keyword?: string;
  user_id?: number;
  module?: string;
  action?: string;
  target_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface AuditLogListResponse {
  items: AuditLogRecord[];
  total: number;
  page: number;
  page_size: number;
}
