import { http } from "@/api/http";
import type { BackupCreatePayload, BackupItem, BackupRestoreResponse } from "@/types/backup";

export function listBackups() {
  return http.get<BackupItem[]>("/backups");
}

export function createBackup(payload: BackupCreatePayload) {
  return http.post<BackupItem>("/backups", payload);
}

export function downloadBackup(filename: string) {
  return http.get<Blob>(`/backups/${encodeURIComponent(filename)}/download`, { responseType: "blob" });
}

export function deleteBackup(filename: string) {
  return http.delete(`/backups/${encodeURIComponent(filename)}`);
}

export function restoreBackup(filename: string) {
  return http.post<BackupRestoreResponse>("/backups/restore", { filename });
}

