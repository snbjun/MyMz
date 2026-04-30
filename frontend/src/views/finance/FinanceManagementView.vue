<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import {
  createFinanceAccount,
  createFinanceCategory,
  createFinanceRecord,
  deleteFinanceAccount,
  deleteFinanceCategory,
  getFinanceRecord,
  listFinanceAccounts,
  listFinanceCategories,
  listFinanceRecords,
  toggleFinanceAccountActive,
  toggleFinanceCategoryActive,
  updateFinanceAccount,
  updateFinanceCategory,
  voidFinanceRecord,
} from "@/api/finance";
import { t } from "@/i18n";
import type {
  FinanceAccount,
  FinanceAccountPayload,
  FinanceAccountType,
  FinanceCategory,
  FinanceCategoryPayload,
  FinanceRecord,
  FinanceRecordStatus,
  FinanceType,
} from "@/types/finance";

const activeTab = ref("records");
const recordsLoading = ref(false);
const accountsLoading = ref(false);
const categoriesLoading = ref(false);
const records = ref<FinanceRecord[]>([]);
const accounts = ref<FinanceAccount[]>([]);
const categories = ref<FinanceCategory[]>([]);
const recordTotal = ref(0);
const recordDialogVisible = ref(false);
const recordDetailVisible = ref(false);
const accountDialogVisible = ref(false);
const categoryDialogVisible = ref(false);
const editingAccountId = ref<number | null>(null);
const editingCategoryId = ref<number | null>(null);
const currentRecord = ref<FinanceRecord | null>(null);
const recordFormRef = ref<FormInstance>();
const accountFormRef = ref<FormInstance>();
const categoryFormRef = ref<FormInstance>();

const query = reactive({
  keyword: "",
  type: "" as FinanceType | "",
  categoryId: undefined as number | undefined,
  accountId: undefined as number | undefined,
  status: "" as FinanceRecordStatus | "",
  dateRange: [] as string[],
  page: 1,
  pageSize: 10,
});

const recordForm = reactive({
  type: "income" as FinanceType,
  record_date: "",
  category_id: undefined as number | undefined,
  account_id: undefined as number | undefined,
  amount: 0,
  summary: "",
  remark: "",
});

const accountForm = reactive({
  name: "",
  type: "cash" as FinanceAccountType,
  opening_balance: 0,
  sort_order: 0,
  is_default: false,
  is_active: true,
  remark: "",
});

const categoryForm = reactive({
  name: "",
  type: "income" as FinanceType,
  sort_order: 0,
  is_default: false,
  is_active: true,
});

const recordRules: FormRules = {
  type: [{ required: true, message: t("financeTypeRequired"), trigger: "change" }],
  record_date: [{ required: true, message: t("financeDateRequired"), trigger: "change" }],
  category_id: [{ required: true, message: t("financeCategoryRequired"), trigger: "change" }],
  account_id: [{ required: true, message: t("financeAccountRequired"), trigger: "change" }],
  amount: [{ required: true, message: t("financeAmountRequired"), trigger: "blur" }],
};

const accountRules: FormRules = {
  name: [{ required: true, message: t("financeAccountNameRequired"), trigger: "blur" }],
};

const categoryRules: FormRules = {
  name: [{ required: true, message: t("financeCategoryNameRequired"), trigger: "blur" }],
  type: [{ required: true, message: t("financeTypeRequired"), trigger: "change" }],
};

const activeAccounts = computed(() => accounts.value.filter((item) => item.is_active));
const recordCategories = computed(() =>
  categories.value.filter((item) => item.type === recordForm.type && item.is_active),
);

function today() {
  return new Date().toISOString().slice(0, 10);
}

function money(value: number) {
  return value.toFixed(2);
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function financeTypeText(value: string) {
  const map: Record<string, string> = {
    income: t("financeIncome"),
    expense: t("financeExpense"),
  };
  return map[value] || value;
}

function accountTypeText(value: string) {
  const map: Record<string, string> = {
    cash: t("financeAccountCash"),
    bank: t("financeAccountBank"),
    wechat: t("financeAccountWechat"),
    alipay: t("financeAccountAlipay"),
    other: t("financeAccountOther"),
  };
  return map[value] || value;
}

function recordStatusText(value: string) {
  const map: Record<string, string> = {
    normal: t("financeRecordNormal"),
    voided: t("financeRecordVoided"),
  };
  return map[value] || value;
}

async function fetchCategories() {
  categoriesLoading.value = true;
  try {
    const response = await listFinanceCategories();
    categories.value = response.data;
  } finally {
    categoriesLoading.value = false;
  }
}

async function fetchAccounts() {
  accountsLoading.value = true;
  try {
    const response = await listFinanceAccounts();
    accounts.value = response.data;
  } finally {
    accountsLoading.value = false;
  }
}

async function fetchRecords() {
  recordsLoading.value = true;
  try {
    const response = await listFinanceRecords({
      keyword: query.keyword || undefined,
      type: query.type || undefined,
      category_id: query.categoryId,
      account_id: query.accountId,
      status: query.status || undefined,
      start_date: query.dateRange[0],
      end_date: query.dateRange[1],
      page: query.page,
      page_size: query.pageSize,
    });
    records.value = response.data.items;
    recordTotal.value = response.data.total;
  } finally {
    recordsLoading.value = false;
  }
}

async function refreshAll() {
  await Promise.all([fetchCategories(), fetchAccounts()]);
  await fetchRecords();
}

async function handleSearch() {
  query.page = 1;
  await fetchRecords();
}

async function handleReset() {
  query.keyword = "";
  query.type = "";
  query.categoryId = undefined;
  query.accountId = undefined;
  query.status = "";
  query.dateRange = [];
  query.page = 1;
  await fetchRecords();
}

function resetRecordForm(type: FinanceType) {
  recordForm.type = type;
  recordForm.record_date = today();
  recordForm.category_id = categories.value.find((item) => item.type === type && item.is_default)?.id;
  recordForm.account_id = activeAccounts.value.find((item) => item.is_default)?.id || activeAccounts.value[0]?.id;
  recordForm.amount = 0;
  recordForm.summary = "";
  recordForm.remark = "";
}

function openRecordDialog(type: FinanceType) {
  resetRecordForm(type);
  recordDialogVisible.value = true;
}

function handleRecordTypeChange() {
  recordForm.category_id = categories.value.find((item) => item.type === recordForm.type && item.is_default)?.id;
}

async function submitRecord() {
  await recordFormRef.value?.validate();
  if (recordForm.amount <= 0) {
    ElMessage.error(t("financeAmountInvalid"));
    return;
  }
  await createFinanceRecord({
    type: recordForm.type,
    record_date: recordForm.record_date,
    category_id: recordForm.category_id as number,
    account_id: recordForm.account_id as number,
    amount: money(recordForm.amount),
    summary: recordForm.summary || null,
    remark: recordForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  recordDialogVisible.value = false;
  await Promise.all([fetchRecords(), fetchAccounts()]);
}

async function openRecordDetail(row: FinanceRecord) {
  const response = await getFinanceRecord(row.id);
  currentRecord.value = response.data;
  recordDetailVisible.value = true;
}

async function handleVoidRecord(row: FinanceRecord) {
  const result = await ElMessageBox.prompt(t("financeVoidReasonPrompt"), t("financeVoidRecord"), {
    inputType: "textarea",
    inputValidator: (value) => Boolean(value?.trim()) || t("financeVoidReasonRequired"),
    type: "warning",
  });
  await voidFinanceRecord(row.id, result.value.trim());
  ElMessage.success(t("saveSuccess"));
  await Promise.all([fetchRecords(), fetchAccounts()]);
}

function resetAccountForm() {
  editingAccountId.value = null;
  accountForm.name = "";
  accountForm.type = "cash";
  accountForm.opening_balance = 0;
  accountForm.sort_order = 0;
  accountForm.is_default = false;
  accountForm.is_active = true;
  accountForm.remark = "";
}

function openAccountCreate() {
  resetAccountForm();
  accountDialogVisible.value = true;
}

function openAccountEdit(row: FinanceAccount) {
  editingAccountId.value = row.id;
  accountForm.name = row.name;
  accountForm.type = row.type;
  accountForm.opening_balance = Number(row.opening_balance);
  accountForm.sort_order = row.sort_order;
  accountForm.is_default = row.is_default;
  accountForm.is_active = row.is_active;
  accountForm.remark = row.remark || "";
  accountDialogVisible.value = true;
}

async function submitAccount() {
  await accountFormRef.value?.validate();
  const payload: FinanceAccountPayload = {
    name: accountForm.name,
    type: accountForm.type,
    opening_balance: money(accountForm.opening_balance),
    sort_order: accountForm.sort_order,
    is_default: accountForm.is_default,
    is_active: accountForm.is_active,
    remark: accountForm.remark || null,
  };
  if (editingAccountId.value) {
    await updateFinanceAccount(editingAccountId.value, payload);
  } else {
    await createFinanceAccount(payload);
  }
  ElMessage.success(t("saveSuccess"));
  accountDialogVisible.value = false;
  await fetchAccounts();
}

async function handleToggleAccount(row: FinanceAccount) {
  await toggleFinanceAccountActive(row.id);
  ElMessage.success(t("toggleSuccess"));
  await fetchAccounts();
}

async function handleDeleteAccount(row: FinanceAccount) {
  await ElMessageBox.confirm(t("financeAccountDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteFinanceAccount(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchAccounts();
}

function resetCategoryForm() {
  editingCategoryId.value = null;
  categoryForm.name = "";
  categoryForm.type = "income";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  categoryForm.is_active = true;
}

function openCategoryCreate() {
  resetCategoryForm();
  categoryDialogVisible.value = true;
}

function openCategoryEdit(row: FinanceCategory) {
  editingCategoryId.value = row.id;
  categoryForm.name = row.name;
  categoryForm.type = row.type;
  categoryForm.sort_order = row.sort_order;
  categoryForm.is_default = row.is_default;
  categoryForm.is_active = row.is_active;
  categoryDialogVisible.value = true;
}

async function submitCategory() {
  await categoryFormRef.value?.validate();
  const payload: FinanceCategoryPayload = { ...categoryForm };
  if (editingCategoryId.value) {
    await updateFinanceCategory(editingCategoryId.value, payload);
  } else {
    await createFinanceCategory(payload);
  }
  ElMessage.success(t("saveSuccess"));
  categoryDialogVisible.value = false;
  await fetchCategories();
}

async function handleToggleCategory(row: FinanceCategory) {
  await toggleFinanceCategoryActive(row.id);
  ElMessage.success(t("toggleSuccess"));
  await fetchCategories();
}

async function handleDeleteCategory(row: FinanceCategory) {
  await ElMessageBox.confirm(t("financeCategoryDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteFinanceCategory(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchCategories();
}

onMounted(refreshAll);
</script>

<template>
  <section class="management-page">
    <el-tabs v-model="activeTab" class="finance-tabs">
      <el-tab-pane :label="t('financeRecords')" name="records">
        <div class="table-toolbar finance-toolbar">
          <el-input v-model="query.keyword" :placeholder="t('financeKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
          <el-select v-model="query.type" :placeholder="t('financeType')" clearable @change="query.categoryId = undefined">
            <el-option :label="t('financeIncome')" value="income" />
            <el-option :label="t('financeExpense')" value="expense" />
          </el-select>
          <el-select v-model="query.categoryId" :placeholder="t('financeCategory')" clearable filterable>
            <el-option
              v-for="item in categories.filter((row) => !query.type || row.type === query.type)"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
          <el-select v-model="query.accountId" :placeholder="t('financeAccount')" clearable filterable>
            <el-option v-for="item in accounts" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-select v-model="query.status" :placeholder="t('status')" clearable>
            <el-option :label="t('financeRecordNormal')" value="normal" />
            <el-option :label="t('financeRecordVoided')" value="voided" />
          </el-select>
          <el-date-picker v-model="query.dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('startDate')" :end-placeholder="t('endDate')" />
          <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
          <el-button @click="handleReset">{{ t("reset") }}</el-button>
          <el-button type="success" @click="openRecordDialog('income')">{{ t("addIncome") }}</el-button>
          <el-button type="warning" @click="openRecordDialog('expense')">{{ t("addExpense") }}</el-button>
        </div>

        <el-table v-loading="recordsLoading" :data="records" border class="data-table" :empty-text="t('noData')">
          <el-table-column prop="record_no" :label="t('financeRecordNo')" min-width="150" />
          <el-table-column prop="record_date" :label="t('date')" min-width="110" />
          <el-table-column :label="t('financeType')" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'income' ? 'success' : 'warning'">{{ financeTypeText(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category_name" :label="t('financeCategory')" min-width="130" />
          <el-table-column prop="account_name" :label="t('financeAccount')" min-width="130" />
          <el-table-column prop="amount" :label="t('amount')" align="right" min-width="110" />
          <el-table-column prop="summary" :label="t('financeSummary')" min-width="160" />
          <el-table-column :label="t('status')" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'normal' ? 'primary' : 'info'">{{ recordStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_by_name" :label="t('operator')" min-width="110" />
          <el-table-column :label="t('createdAt')" min-width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column :label="t('actions')" fixed="right" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openRecordDetail(row)">{{ t("detail") }}</el-button>
              <el-button v-if="row.status === 'normal'" size="small" type="danger" @click="handleVoidRecord(row)">{{ t("financeVoidRecord") }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="query.page"
            v-model:page-size="query.pageSize"
            :total="recordTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchRecords"
            @current-change="fetchRecords"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('financeAccounts')" name="accounts">
        <div class="table-toolbar">
          <el-button type="primary" @click="openAccountCreate">{{ t("addFinanceAccount") }}</el-button>
        </div>
        <el-table v-loading="accountsLoading" :data="accounts" border class="data-table" :empty-text="t('noData')">
          <el-table-column prop="name" :label="t('financeAccountName')" min-width="150" />
          <el-table-column :label="t('financeAccountType')" min-width="120">
            <template #default="{ row }">{{ accountTypeText(row.type) }}</template>
          </el-table-column>
          <el-table-column prop="opening_balance" :label="t('openingBalance')" align="right" min-width="120" />
          <el-table-column prop="current_balance" :label="t('currentBalance')" align="right" min-width="120" />
          <el-table-column :label="t('status')" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? t("enabled") : t("disabled") }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" :label="t('sortOrder')" width="90" />
          <el-table-column prop="remark" :label="t('remark')" min-width="160" />
          <el-table-column :label="t('createdAt')" min-width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column :label="t('actions')" fixed="right" width="220">
            <template #default="{ row }">
              <el-button size="small" @click="openAccountEdit(row)">{{ t("edit") }}</el-button>
              <el-button size="small" @click="handleToggleAccount(row)">{{ row.is_active ? t("disable") : t("enable") }}</el-button>
              <el-button size="small" type="danger" @click="handleDeleteAccount(row)">{{ t("delete") }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('financeCategories')" name="categories">
        <div class="table-toolbar">
          <el-button type="primary" @click="openCategoryCreate">{{ t("addFinanceCategory") }}</el-button>
        </div>
        <el-table v-loading="categoriesLoading" :data="categories" border class="data-table" :empty-text="t('noData')">
          <el-table-column prop="name" :label="t('categoryName')" min-width="150" />
          <el-table-column :label="t('financeType')" min-width="100">
            <template #default="{ row }">{{ financeTypeText(row.type) }}</template>
          </el-table-column>
          <el-table-column :label="t('status')" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? t("enabled") : t("disabled") }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('defaultCategory')" width="110">
            <template #default="{ row }">{{ row.is_default ? t("yes") : t("no") }}</template>
          </el-table-column>
          <el-table-column prop="sort_order" :label="t('sortOrder')" width="90" />
          <el-table-column :label="t('createdAt')" min-width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column :label="t('actions')" fixed="right" width="220">
            <template #default="{ row }">
              <el-button size="small" @click="openCategoryEdit(row)">{{ t("edit") }}</el-button>
              <el-button size="small" @click="handleToggleCategory(row)">{{ row.is_active ? t("disable") : t("enable") }}</el-button>
              <el-button size="small" type="danger" @click="handleDeleteCategory(row)">{{ t("delete") }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="recordDialogVisible" :title="recordForm.type === 'income' ? t('addIncome') : t('addExpense')" width="560px">
      <el-form ref="recordFormRef" :model="recordForm" :rules="recordRules" label-width="100px">
        <el-form-item :label="t('financeType')" prop="type">
          <el-select v-model="recordForm.type" class="form-wide-control" @change="handleRecordTypeChange">
            <el-option :label="t('financeIncome')" value="income" />
            <el-option :label="t('financeExpense')" value="expense" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('date')" prop="record_date">
          <el-date-picker v-model="recordForm.record_date" type="date" value-format="YYYY-MM-DD" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('financeCategory')" prop="category_id">
          <el-select v-model="recordForm.category_id" filterable class="form-wide-control">
            <el-option v-for="item in recordCategories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('financeAccount')" prop="account_id">
          <el-select v-model="recordForm.account_id" filterable class="form-wide-control">
            <el-option v-for="item in activeAccounts" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('amount')" prop="amount">
          <el-input-number v-model="recordForm.amount" :min="0.01" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('financeSummary')">
          <el-input v-model="recordForm.summary" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="recordForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitRecord">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="recordDetailVisible" :title="t('financeRecordDetail')" width="720px">
      <el-descriptions v-if="currentRecord" :column="2" border>
        <el-descriptions-item :label="t('financeRecordNo')">{{ currentRecord.record_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('date')">{{ currentRecord.record_date }}</el-descriptions-item>
        <el-descriptions-item :label="t('financeType')">{{ financeTypeText(currentRecord.type) }}</el-descriptions-item>
        <el-descriptions-item :label="t('financeCategory')">{{ currentRecord.category_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('financeAccount')">{{ currentRecord.account_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('amount')">{{ currentRecord.amount }}</el-descriptions-item>
        <el-descriptions-item :label="t('status')">{{ recordStatusText(currentRecord.status) }}</el-descriptions-item>
        <el-descriptions-item :label="t('operator')">{{ currentRecord.created_by_name || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('financeSummary')">{{ currentRecord.summary || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('remark')">{{ currentRecord.remark || "-" }}</el-descriptions-item>
        <el-descriptions-item :label="t('financeVoidReason')">{{ currentRecord.void_reason || "-" }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="accountDialogVisible" :title="editingAccountId ? t('editFinanceAccount') : t('addFinanceAccount')" width="560px">
      <el-form ref="accountFormRef" :model="accountForm" :rules="accountRules" label-width="100px">
        <el-form-item :label="t('financeAccountName')" prop="name">
          <el-input v-model="accountForm.name" />
        </el-form-item>
        <el-form-item :label="t('financeAccountType')">
          <el-select v-model="accountForm.type" class="form-wide-control">
            <el-option :label="t('financeAccountCash')" value="cash" />
            <el-option :label="t('financeAccountBank')" value="bank" />
            <el-option :label="t('financeAccountWechat')" value="wechat" />
            <el-option :label="t('financeAccountAlipay')" value="alipay" />
            <el-option :label="t('financeAccountOther')" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('openingBalance')">
          <el-input-number v-model="accountForm.opening_balance" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('sortOrder')">
          <el-input-number v-model="accountForm.sort_order" :min="0" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('defaultAccount')">
          <el-switch v-model="accountForm.is_default" />
        </el-form-item>
        <el-form-item :label="t('isActive')">
          <el-switch v-model="accountForm.is_active" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="accountForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitAccount">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="categoryDialogVisible" :title="editingCategoryId ? t('editFinanceCategory') : t('addFinanceCategory')" width="520px">
      <el-form ref="categoryFormRef" :model="categoryForm" :rules="categoryRules" label-width="100px">
        <el-form-item :label="t('categoryName')" prop="name">
          <el-input v-model="categoryForm.name" />
        </el-form-item>
        <el-form-item :label="t('financeType')" prop="type">
          <el-select v-model="categoryForm.type" class="form-wide-control">
            <el-option :label="t('financeIncome')" value="income" />
            <el-option :label="t('financeExpense')" value="expense" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('sortOrder')">
          <el-input-number v-model="categoryForm.sort_order" :min="0" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('defaultCategory')">
          <el-switch v-model="categoryForm.is_default" />
        </el-form-item>
        <el-form-item :label="t('isActive')">
          <el-switch v-model="categoryForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitCategory">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>
  </section>
</template>
