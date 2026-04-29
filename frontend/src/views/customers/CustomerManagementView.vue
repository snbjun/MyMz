<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import {
  createCustomer,
  createCustomerCategory,
  deleteCustomer,
  deleteCustomerCategory,
  listCustomerCategories,
  listCustomers,
  toggleCustomerActive,
  updateCustomer,
  updateCustomerCategory,
} from "@/api/customers";
import { t } from "@/i18n";
import type { CustomerCategory, CustomerPayload, CustomerRecord } from "@/types/customer";

const loading = ref(false);
const categoriesLoading = ref(false);
const tableData = ref<CustomerRecord[]>([]);
const categories = ref<CustomerCategory[]>([]);
const total = ref(0);
const customerDialogVisible = ref(false);
const categoryDialogVisible = ref(false);
const customerEditing = ref(false);
const categoryEditingId = ref<number | null>(null);
const customerFormRef = ref<FormInstance>();
const categoryFormRef = ref<FormInstance>();

const query = reactive({
  keyword: "",
  categoryId: undefined as number | undefined,
  activeStatus: "" as "" | "true" | "false",
  page: 1,
  pageSize: 10,
});

const customerForm = reactive({
  id: 0,
  code: "",
  name: "",
  category_id: undefined as number | undefined,
  contact_name: "",
  phone: "",
  backup_phone: "",
  email: "",
  wechat: "",
  address: "",
  tax_number: "",
  opening_receivable: 0,
  current_receivable: 0,
  credit_limit: 0,
  is_active: true,
  remark: "",
});

const categoryForm = reactive({
  name: "",
  sort_order: 0,
  is_default: false,
});

const customerRules: FormRules = {
  name: [{ required: true, message: t("customerNameRequired"), trigger: "blur" }],
};

const categoryRules: FormRules = {
  name: [{ required: true, message: t("categoryNameRequired"), trigger: "blur" }],
};

const defaultCategoryId = computed(() => categories.value.find((item) => item.is_default)?.id);

function money(value: number) {
  return value.toFixed(2);
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function resetCustomerForm() {
  customerForm.id = 0;
  customerForm.code = "";
  customerForm.name = "";
  customerForm.category_id = defaultCategoryId.value;
  customerForm.contact_name = "";
  customerForm.phone = "";
  customerForm.backup_phone = "";
  customerForm.email = "";
  customerForm.wechat = "";
  customerForm.address = "";
  customerForm.tax_number = "";
  customerForm.opening_receivable = 0;
  customerForm.current_receivable = 0;
  customerForm.credit_limit = 0;
  customerForm.is_active = true;
  customerForm.remark = "";
}

function buildCustomerPayload(): CustomerPayload {
  return {
    code: customerForm.code || null,
    name: customerForm.name,
    category_id: customerForm.category_id || null,
    contact_name: customerForm.contact_name || null,
    phone: customerForm.phone || null,
    backup_phone: customerForm.backup_phone || null,
    email: customerForm.email || null,
    wechat: customerForm.wechat || null,
    address: customerForm.address || null,
    tax_number: customerForm.tax_number || null,
    opening_receivable: money(customerForm.opening_receivable),
    current_receivable: money(customerForm.current_receivable),
    credit_limit: money(customerForm.credit_limit),
    remark: customerForm.remark || null,
    is_active: customerForm.is_active,
  };
}

async function fetchCategories() {
  categoriesLoading.value = true;
  try {
    const response = await listCustomerCategories();
    categories.value = response.data;
  } finally {
    categoriesLoading.value = false;
  }
}

async function fetchCustomers() {
  loading.value = true;
  try {
    const response = await listCustomers({
      keyword: query.keyword || undefined,
      category_id: query.categoryId,
      is_active: query.activeStatus === "" ? undefined : query.activeStatus === "true",
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
  await fetchCustomers();
}

async function handleReset() {
  query.keyword = "";
  query.categoryId = undefined;
  query.activeStatus = "";
  query.page = 1;
  await fetchCustomers();
}

function openCreateCustomerDialog() {
  customerEditing.value = false;
  resetCustomerForm();
  customerDialogVisible.value = true;
}

function openEditCustomerDialog(row: CustomerRecord) {
  customerEditing.value = true;
  customerForm.id = row.id;
  customerForm.code = row.code || "";
  customerForm.name = row.name;
  customerForm.category_id = row.category_id || undefined;
  customerForm.contact_name = row.contact_name || "";
  customerForm.phone = row.phone || "";
  customerForm.backup_phone = row.backup_phone || "";
  customerForm.email = row.email || "";
  customerForm.wechat = row.wechat || "";
  customerForm.address = row.address || "";
  customerForm.tax_number = row.tax_number || "";
  customerForm.opening_receivable = Number(row.opening_receivable);
  customerForm.current_receivable = Number(row.current_receivable);
  customerForm.credit_limit = Number(row.credit_limit);
  customerForm.is_active = row.is_active;
  customerForm.remark = row.remark || "";
  customerDialogVisible.value = true;
}

async function saveCustomer() {
  await customerFormRef.value?.validate();
  if (customerEditing.value) {
    await updateCustomer(customerForm.id, buildCustomerPayload());
  } else {
    await createCustomer(buildCustomerPayload());
  }
  ElMessage.success(t("saveSuccess"));
  customerDialogVisible.value = false;
  await fetchCustomers();
}

async function handleToggle(row: CustomerRecord) {
  await toggleCustomerActive(row.id);
  ElMessage.success(t("toggleSuccess"));
  await fetchCustomers();
}

async function handleDelete(row: CustomerRecord) {
  await ElMessageBox.confirm(t("customerDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteCustomer(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchCustomers();
}

function openCategoryDialog() {
  categoryEditingId.value = null;
  categoryForm.name = "";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  categoryDialogVisible.value = true;
}

function editCategory(row: CustomerCategory) {
  categoryEditingId.value = row.id;
  categoryForm.name = row.name;
  categoryForm.sort_order = row.sort_order;
  categoryForm.is_default = row.is_default;
}

async function saveCategory() {
  await categoryFormRef.value?.validate();
  const payload = {
    name: categoryForm.name,
    sort_order: categoryForm.sort_order,
    is_default: categoryForm.is_default,
  };
  if (categoryEditingId.value) {
    await updateCustomerCategory(categoryEditingId.value, payload);
  } else {
    await createCustomerCategory(payload);
  }
  ElMessage.success(t("saveSuccess"));
  categoryEditingId.value = null;
  categoryForm.name = "";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  await fetchCategories();
}

async function removeCategory(row: CustomerCategory) {
  await ElMessageBox.confirm(t("categoryDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteCustomerCategory(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchCategories();
  await fetchCustomers();
}

onMounted(async () => {
  await fetchCategories();
  await fetchCustomers();
});
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar customer-toolbar">
      <el-input v-model="query.keyword" :placeholder="t('customerKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      <el-select v-model="query.categoryId" :placeholder="t('customerCategory')" clearable>
        <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="query.activeStatus" :placeholder="t('isActive')" clearable>
        <el-option :label="t('enabled')" value="true" />
        <el-option :label="t('disabled')" value="false" />
      </el-select>
      <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
      <el-button type="success" @click="openCreateCustomerDialog">{{ t("addCustomer") }}</el-button>
      <el-button @click="openCategoryDialog">{{ t("categoryManage") }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border class="data-table" :empty-text="t('noData')">
      <el-table-column prop="code" :label="t('customerCode')" min-width="120" />
      <el-table-column prop="name" :label="t('customerName')" min-width="150" />
      <el-table-column prop="category_name" :label="t('customerCategory')" min-width="120" />
      <el-table-column prop="contact_name" :label="t('contactName')" min-width="110" />
      <el-table-column prop="phone" :label="t('phone')" min-width="130" />
      <el-table-column prop="address" :label="t('address')" min-width="180" show-overflow-tooltip />
      <el-table-column prop="opening_receivable" :label="t('openingReceivable')" min-width="120" align="right" />
      <el-table-column prop="current_receivable" :label="t('currentReceivable')" min-width="120" align="right" />
      <el-table-column prop="is_active" :label="t('status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? t("enabled") : t("disabled") }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('createdAt')" min-width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('actions')" fixed="right" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="openEditCustomerDialog(row)">{{ t("edit") }}</el-button>
          <el-button size="small" @click="handleToggle(row)">{{ row.is_active ? t("disable") : t("enable") }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">{{ t("delete") }}</el-button>
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
        @size-change="fetchCustomers"
        @current-change="fetchCustomers"
      />
    </div>

    <el-drawer v-model="customerDialogVisible" :title="customerEditing ? t('editCustomer') : t('addCustomer')" size="560px">
      <el-form ref="customerFormRef" :model="customerForm" :rules="customerRules" label-width="110px">
        <el-form-item :label="t('customerName')" prop="name">
          <el-input v-model="customerForm.name" />
        </el-form-item>
        <el-form-item :label="t('customerCode')">
          <el-input v-model="customerForm.code" />
        </el-form-item>
        <el-form-item :label="t('customerCategory')">
          <el-select v-model="customerForm.category_id" clearable class="form-wide-control">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('contactName')">
          <el-input v-model="customerForm.contact_name" />
        </el-form-item>
        <el-form-item :label="t('phone')">
          <el-input v-model="customerForm.phone" />
        </el-form-item>
        <el-form-item :label="t('backupPhone')">
          <el-input v-model="customerForm.backup_phone" />
        </el-form-item>
        <el-form-item :label="t('email')">
          <el-input v-model="customerForm.email" />
        </el-form-item>
        <el-form-item :label="t('wechat')">
          <el-input v-model="customerForm.wechat" />
        </el-form-item>
        <el-form-item :label="t('address')">
          <el-input v-model="customerForm.address" />
        </el-form-item>
        <el-form-item :label="t('taxNumber')">
          <el-input v-model="customerForm.tax_number" />
        </el-form-item>
        <el-form-item :label="t('openingReceivable')">
          <el-input-number v-model="customerForm.opening_receivable" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('currentReceivable')">
          <el-input-number v-model="customerForm.current_receivable" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('creditLimit')">
          <el-input-number v-model="customerForm.credit_limit" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('isActive')">
          <el-switch v-model="customerForm.is_active" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="customerForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="saveCustomer">{{ t("confirm") }}</el-button>
      </template>
    </el-drawer>

    <el-dialog v-model="categoryDialogVisible" :title="t('categoryManage')" width="620px">
      <el-form ref="categoryFormRef" :model="categoryForm" :rules="categoryRules" inline>
        <el-form-item :label="t('categoryName')" prop="name">
          <el-input v-model="categoryForm.name" />
        </el-form-item>
        <el-form-item :label="t('sortOrder')">
          <el-input-number v-model="categoryForm.sort_order" :precision="0" />
        </el-form-item>
        <el-form-item :label="t('defaultCategory')">
          <el-switch v-model="categoryForm.is_default" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveCategory">{{ categoryEditingId ? t("confirm") : t("add") }}</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="categoriesLoading" :data="categories" border :empty-text="t('noData')">
        <el-table-column prop="name" :label="t('categoryName')" />
        <el-table-column prop="sort_order" :label="t('sortOrder')" width="110" />
        <el-table-column :label="t('defaultCategory')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">{{ t("yes") }}</el-tag>
            <span v-else>{{ t("no") }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('actions')" width="170">
          <template #default="{ row }">
            <el-button size="small" @click="editCategory(row)">{{ t("edit") }}</el-button>
            <el-button size="small" type="danger" :disabled="row.is_default" @click="removeCategory(row)">{{ t("delete") }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </section>
</template>
