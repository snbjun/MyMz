<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { getAuditLog, listAuditLogs } from "@/api/auditLogs";
import { t } from "@/i18n";
import type { AuditLogRecord } from "@/types/auditLog";

const loading = ref(false);
const tableData = ref<AuditLogRecord[]>([]);
const total = ref(0);
const detailVisible = ref(false);
const currentLog = ref<AuditLogRecord | null>(null);

const query = reactive({
  keyword: "",
  userId: undefined as number | undefined,
  module: "",
  action: "",
  targetType: "",
  dateRange: [] as string[],
  page: 1,
  pageSize: 20,
});

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

async function fetchLogs() {
  loading.value = true;
  try {
    const response = await listAuditLogs({
      keyword: query.keyword || undefined,
      user_id: query.userId,
      module: query.module || undefined,
      action: query.action || undefined,
      target_type: query.targetType || undefined,
      start_date: query.dateRange[0],
      end_date: query.dateRange[1],
      page: query.page,
      page_size: query.pageSize,
    });
    tableData.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
}

async function handleSearch() {
  query.page = 1;
  await fetchLogs();
}

async function handleReset() {
  query.keyword = "";
  query.userId = undefined;
  query.module = "";
  query.action = "";
  query.targetType = "";
  query.dateRange = [];
  query.page = 1;
  await fetchLogs();
}

async function openDetail(row: AuditLogRecord) {
  const response = await getAuditLog(row.id);
  currentLog.value = response.data;
  detailVisible.value = true;
}

onMounted(fetchLogs);
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar audit-toolbar">
      <el-input v-model="query.keyword" :placeholder="t('auditKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      <el-input-number v-model="query.userId" :placeholder="t('auditUserId')" :min="1" clearable />
      <el-input v-model="query.module" :placeholder="t('auditModule')" clearable />
      <el-input v-model="query.action" :placeholder="t('auditAction')" clearable />
      <el-input v-model="query.targetType" :placeholder="t('auditTargetType')" clearable />
      <el-date-picker v-model="query.dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('startDate')" :end-placeholder="t('endDate')" />
      <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border class="data-table" :empty-text="t('noData')">
      <el-table-column :label="t('date')" min-width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="username" :label="t('username')" min-width="120" />
      <el-table-column prop="module" :label="t('auditModule')" min-width="120" />
      <el-table-column prop="action" :label="t('auditAction')" min-width="120" />
      <el-table-column prop="target_type" :label="t('auditTargetType')" min-width="120" />
      <el-table-column prop="target_label" :label="t('auditTarget')" min-width="160" />
      <el-table-column prop="ip_address" :label="t('auditIpAddress')" min-width="130" />
      <el-table-column prop="summary" :label="t('auditSummary')" min-width="240" />
      <el-table-column :label="t('actions')" fixed="right" width="90">
        <template #default="{ row }">
          <el-button size="small" @click="openDetail(row)">{{ t("detail") }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchLogs"
        @current-change="fetchLogs"
      />
    </div>

    <el-dialog v-model="detailVisible" :title="t('auditLogDetail')" width="720px">
      <el-descriptions v-if="currentLog" :column="2" border>
        <el-descriptions-item :label="t('username')">{{ currentLog.username || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditModule')">{{ currentLog.module }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditAction')">{{ currentLog.action }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditTargetType')">{{ currentLog.target_type || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditTargetId')">{{ currentLog.target_id || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditTarget')">{{ currentLog.target_label || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditMethod')">{{ currentLog.method || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditPath')">{{ currentLog.path || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditIpAddress')">{{ currentLog.ip_address || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditUserAgent')">{{ currentLog.user_agent || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('auditSummary')" :span="2">{{ currentLog.summary }}</el-descriptions-item>
        <el-descriptions-item :label="t('createdAt')" :span="2">{{ formatDate(currentLog.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </section>
</template>
