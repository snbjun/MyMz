<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import {
  createSupplier,
  createSupplierCategory,
  deleteSupplier,
  deleteSupplierCategory,
  listSupplierCategories,
  listSuppliers,
  toggleSupplierActive,
  updateSupplier,
  updateSupplierCategory,
} from "@/api/suppliers";
import { t } from "@/i18n";
import type { SupplierCategory, SupplierPayload, SupplierRecord } from "@/types/supplier";

const loading = ref(false);
const categoriesLoading = ref(false);
const tableData = ref<SupplierRecord[]>([]);
const categories = ref<SupplierCategory[]>([]);
const total = ref(0);
const supplierDialogVisible = ref(false);
const categoryDialogVisible = ref(false);
const supplierEditing = ref(false);
const categoryEditingId = ref<number | null>(null);
const supplierFormRef = ref<FormInstance>();
const categoryFormRef = ref<FormInstance>();

const query = reactive({
  keyword: "",
  categoryId: undefined as number | undefined,
  activeStatus: "" as "" | "true" | "false",
  page: 1,
  pageSize: 10,
});

const supplierForm = reactive({
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
  opening_payable: 0,
  current_payable: 0,
  credit_limit: 0,
  is_active: true,
  remark: "",
});

const categoryForm = reactive({
  name: "",
  sort_order: 0,
  is_default: false,
});

const supplierRules: FormRules = {
  name: [{ required: true, message: t("supplierNameRequired"), trigger: "blur" }],
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

function resetSupplierForm() {
  supplierForm.id = 0;
  supplierForm.code = "";
  supplierForm.name = "";
  supplierForm.category_id = defaultCategoryId.value;
  supplierForm.contact_name = "";
  supplierForm.phone = "";
  supplierForm.backup_phone = "";
  supplierForm.email = "";
  supplierForm.wechat = "";
  supplierForm.address = "";
  supplierForm.tax_number = "";
  supplierForm.opening_payable = 0;
  supplierForm.current_payable = 0;
  supplierForm.credit_limit = 0;
  supplierForm.is_active = true;
  supplierForm.remark = "";
}

function buildSupplierPayload(): SupplierPayload {
  return {
    code: supplierForm.code || null,
    name: supplierForm.name,
    category_id: supplierForm.category_id || null,
    contact_name: supplierForm.contact_name || null,
    phone: supplierForm.phone || null,
    backup_phone: supplierForm.backup_phone || null,
    email: supplierForm.email || null,
    wechat: supplierForm.wechat || null,
    address: supplierForm.address || null,
    tax_number: supplierForm.tax_number || null,
    opening_payable: money(supplierForm.opening_payable),
    current_payable: money(supplierForm.current_payable),
    credit_limit: money(supplierForm.credit_limit),
    remark: supplierForm.remark || null,
    is_active: supplierForm.is_active,
  };
}

async function fetchCategories() {
  categoriesLoading.value = true;
  try {
    const response = await listSupplierCategories();
    categories.value = response.data;
  } finally {
    categoriesLoading.value = false;
  }
}

async function fetchSuppliers() {
  loading.value = true;
  try {
    const response = await listSuppliers({
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
  await fetchSuppliers();
}

async function handleReset() {
  query.keyword = "";
  query.categoryId = undefined;
  query.activeStatus = "";
  query.page = 1;
  await fetchSuppliers();
}

function openCreateSupplierDialog() {
  supplierEditing.value = false;
  resetSupplierForm();
  supplierDialogVisible.value = true;
}

function openEditSupplierDialog(row: SupplierRecord) {
  supplierEditing.value = true;
  supplierForm.id = row.id;
  supplierForm.code = row.code || "";
  supplierForm.name = row.name;
  supplierForm.category_id = row.category_id || undefined;
  supplierForm.contact_name = row.contact_name || "";
  supplierForm.phone = row.phone || "";
  supplierForm.backup_phone = row.backup_phone || "";
  supplierForm.email = row.email || "";
  supplierForm.wechat = row.wechat || "";
  supplierForm.address = row.address || "";
  supplierForm.tax_number = row.tax_number || "";
  supplierForm.opening_payable = Number(row.opening_payable);
  supplierForm.current_payable = Number(row.current_payable);
  supplierForm.credit_limit = Number(row.credit_limit);
  supplierForm.is_active = row.is_active;
  supplierForm.remark = row.remark || "";
  supplierDialogVisible.value = true;
}

async function saveSupplier() {
  await supplierFormRef.value?.validate();
  if (supplierEditing.value) {
    await updateSupplier(supplierForm.id, buildSupplierPayload());
  } else {
    await createSupplier(buildSupplierPayload());
  }
  ElMessage.success(t("saveSuccess"));
  supplierDialogVisible.value = false;
  await fetchSuppliers();
}

async function handleToggle(row: SupplierRecord) {
  await toggleSupplierActive(row.id);
  ElMessage.success(t("toggleSuccess"));
  await fetchSuppliers();
}

async function handleDelete(row: SupplierRecord) {
  await ElMessageBox.confirm(t("supplierDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteSupplier(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchSuppliers();
}

function openCategoryDialog() {
  categoryEditingId.value = null;
  categoryForm.name = "";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  categoryDialogVisible.value = true;
}

function editCategory(row: SupplierCategory) {
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
    await updateSupplierCategory(categoryEditingId.value, payload);
  } else {
    await createSupplierCategory(payload);
  }
  ElMessage.success(t("saveSuccess"));
  categoryEditingId.value = null;
  categoryForm.name = "";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  await fetchCategories();
}

async function removeCategory(row: SupplierCategory) {
  await ElMessageBox.confirm(t("categoryDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteSupplierCategory(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchCategories();
  await fetchSuppliers();
}

onMounted(async () => {
  await fetchCategories();
  await fetchSuppliers();
});
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar supplier-toolbar">
      <el-input v-model="query.keyword" :placeholder="t('supplierKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      <el-select v-model="query.categoryId" :placeholder="t('supplierCategory')" clearable>
        <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="query.activeStatus" :placeholder="t('isActive')" clearable>
        <el-option :label="t('enabled')" value="true" />
        <el-option :label="t('disabled')" value="false" />
      </el-select>
      <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
      <el-button type="success" @click="openCreateSupplierDialog">{{ t("addSupplier") }}</el-button>
      <el-button @click="openCategoryDialog">{{ t("categoryManage") }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border class="data-table" :empty-text="t('noData')">
      <el-table-column prop="code" :label="t('supplierCode')" min-width="120" />
      <el-table-column prop="name" :label="t('supplierName')" min-width="150" />
      <el-table-column prop="category_name" :label="t('supplierCategory')" min-width="120" />
      <el-table-column prop="contact_name" :label="t('contactName')" min-width="110" />
      <el-table-column prop="phone" :label="t('phone')" min-width="130" />
      <el-table-column prop="address" :label="t('address')" min-width="180" show-overflow-tooltip />
      <el-table-column prop="opening_payable" :label="t('openingPayable')" min-width="120" align="right" />
      <el-table-column prop="current_payable" :label="t('currentPayable')" min-width="120" align="right" />
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
          <el-button size="small" @click="openEditSupplierDialog(row)">{{ t("edit") }}</el-button>
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
        @size-change="fetchSuppliers"
        @current-change="fetchSuppliers"
      />
    </div>

    <el-drawer v-model="supplierDialogVisible" :title="supplierEditing ? t('editSupplier') : t('addSupplier')" size="560px">
      <el-form ref="supplierFormRef" :model="supplierForm" :rules="supplierRules" label-width="110px">
        <el-form-item :label="t('supplierName')" prop="name">
          <el-input v-model="supplierForm.name" />
        </el-form-item>
        <el-form-item :label="t('supplierCode')">
          <el-input v-model="supplierForm.code" />
        </el-form-item>
        <el-form-item :label="t('supplierCategory')">
          <el-select v-model="supplierForm.category_id" clearable class="form-wide-control">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('contactName')">
          <el-input v-model="supplierForm.contact_name" />
        </el-form-item>
        <el-form-item :label="t('phone')">
          <el-input v-model="supplierForm.phone" />
        </el-form-item>
        <el-form-item :label="t('backupPhone')">
          <el-input v-model="supplierForm.backup_phone" />
        </el-form-item>
        <el-form-item :label="t('email')">
          <el-input v-model="supplierForm.email" />
        </el-form-item>
        <el-form-item :label="t('wechat')">
          <el-input v-model="supplierForm.wechat" />
        </el-form-item>
        <el-form-item :label="t('address')">
          <el-input v-model="supplierForm.address" />
        </el-form-item>
        <el-form-item :label="t('taxNumber')">
          <el-input v-model="supplierForm.tax_number" />
        </el-form-item>
        <el-form-item :label="t('openingPayable')">
          <el-input-number v-model="supplierForm.opening_payable" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('currentPayable')">
          <el-input-number v-model="supplierForm.current_payable" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('creditLimit')">
          <el-input-number v-model="supplierForm.credit_limit" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('isActive')">
          <el-switch v-model="supplierForm.is_active" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="supplierForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supplierDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="saveSupplier">{{ t("confirm") }}</el-button>
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

