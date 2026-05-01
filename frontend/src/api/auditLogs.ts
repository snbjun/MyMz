import { http } from "@/api/http";
import type { AuditLogListParams, AuditLogListResponse, AuditLogRecord } from "@/types/auditLog";

export function listAuditLogs(params: AuditLogListParams = {}) {
  return http.get<AuditLogListResponse>("/audit-logs", { params });
}

export function getAuditLog(id: number) {
  return http.get<AuditLogRecord>(`/audit-logs/${id}`);
}
