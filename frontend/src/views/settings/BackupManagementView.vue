<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { createBackup, deleteBackup, downloadBackup, listBackups, restoreBackup } from "@/api/backups";
import { t } from "@/i18n";
import type { BackupItem } from "@/types/backup";

const loading = ref(false);
const backups = ref<BackupItem[]>([]);

function formatDate(value: string) {
  return value ? new Date(value).toLocaleString() : "-";
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

function kindText(kind: BackupItem["kind"]) {
  const map: Record<BackupItem["kind"], string> = {
    manual: t("backupKindManual"),
    before_restore: t("backupKindBeforeRestore"),
    unknown: t("backupKindUnknown"),
  };
  return map[kind];
}

async function fetchBackups() {
  loading.value = true;
  try {
    const response = await listBackups();
    backups.value = response.data;
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  await createBackup({ note: t("manualBackupNote") });
  ElMessage.success(t("backupCreateSuccess"));
  await fetchBackups();
}

async function handleDownload(row: BackupItem) {
  const response = await downloadBackup(row.filename);
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = row.filename;
  link.click();
  URL.revokeObjectURL(url);
}

async function handleDelete(row: BackupItem) {
  await ElMessageBox.confirm(t("backupDeleteConfirm"), t("confirm"), { type: "warning" });
  await deleteBackup(row.filename);
  ElMessage.success(t("deleteSuccess"));
  await fetchBackups();
}

async function handleRestore(row: BackupItem) {
  await ElMessageBox.confirm(t("backupRestoreConfirm"), t("backupRestore"), {
    type: "warning",
    confirmButtonText: t("confirm"),
    cancelButtonText: t("cancel"),
  });
  const response = await restoreBackup(row.filename);
  ElMessage.success(`${t("backupRestoreSuccess")} ${response.data.safety_backup_filename}`);
  await fetchBackups();
}

onMounted(fetchBackups);
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar">
      <div>
        <h2>{{ t("backupRestore") }}</h2>
        <p class="page-hint">{{ t("backupRestoreHint") }}</p>
      </div>
      <el-button type="primary" @click="handleCreate">{{ t("createBackup") }}</el-button>
    </div>

    <el-alert class="backup-alert" type="warning" :closable="false" :title="t('backupRestoreWarning')" />

    <el-table v-loading="loading" :data="backups" border :empty-text="t('noData')">
      <el-table-column prop="filename" :label="t('backupFilename')" min-width="280" />
      <el-table-column :label="t('backupKind')" width="140">
        <template #default="{ row }">{{ kindText(row.kind) }}</template>
      </el-table-column>
      <el-table-column :label="t('backupSize')" width="130" align="right">
        <template #default="{ row }">{{ formatSize(row.size) }}</template>
      </el-table-column>
      <el-table-column :label="t('createdAt')" min-width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('actions')" fixed="right" width="260">
        <template #default="{ row }">
          <el-button size="small" @click="handleDownload(row)">{{ t("downloadBackup") }}</el-button>
          <el-button size="small" type="warning" @click="handleRestore(row)">{{ t("backupRestore") }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">{{ t("delete") }}</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
