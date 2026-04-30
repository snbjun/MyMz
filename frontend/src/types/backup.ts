export interface BackupItem {
  filename: string;
  size: number;
  created_at: string;
  kind: "manual" | "before_restore" | "unknown";
}

export interface BackupCreatePayload {
  note?: string | null;
}

export interface BackupRestoreResponse {
  restored_filename: string;
  safety_backup_filename: string;
  message: string;
}

