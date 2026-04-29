<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import {
  createUser,
  deleteUser,
  listUsers,
  resetUserPassword,
  toggleUserActive,
  updateUser,
  type UserRecord,
} from "@/api/users";
import { t } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const canManage = computed(() => authStore.user?.is_superuser === true);
const loading = ref(false);
const tableData = ref<UserRecord[]>([]);
const total = ref(0);
const dialogVisible = ref(false);
const dialogEditing = ref(false);
const formRef = ref<FormInstance>();

const query = reactive({
  keyword: "",
  page: 1,
  pageSize: 10,
});

const form = reactive({
  id: 0,
  username: "",
  display_name: "",
  password: "",
  role: "staff",
  is_active: true,
  is_superuser: false,
});

const passwordValidator = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!dialogEditing.value && (!value || value.length < 6)) {
    callback(new Error(t("passwordMin")));
    return;
  }
  callback();
};

const rules: FormRules = {
  username: [{ required: true, message: t("usernameRequired"), trigger: "blur" }],
  display_name: [{ required: true, message: t("displayName"), trigger: "blur" }],
  password: [{ validator: passwordValidator, trigger: "blur" }],
};

async function fetchUsers() {
  if (!canManage.value) {
    return;
  }
  loading.value = true;
  try {
    const response = await listUsers({
      keyword: query.keyword,
      page: query.page,
      page_size: query.pageSize,
    });
    tableData.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
}

function resetForm() {
  form.id = 0;
  form.username = "";
  form.display_name = "";
  form.password = "";
  form.role = "staff";
  form.is_active = true;
  form.is_superuser = false;
}

function openCreateDialog() {
  dialogEditing.value = false;
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(row: UserRecord) {
  dialogEditing.value = true;
  form.id = row.id;
  form.username = row.username;
  form.display_name = row.display_name;
  form.password = "";
  form.role = row.role;
  form.is_active = row.is_active;
  form.is_superuser = row.is_superuser;
  dialogVisible.value = true;
}

async function saveUser() {
  await formRef.value?.validate();
  if (dialogEditing.value) {
    await updateUser(form.id, {
      display_name: form.display_name,
      role: form.role,
      is_active: form.is_active,
      is_superuser: form.is_superuser,
    });
  } else {
    await createUser({
      username: form.username,
      display_name: form.display_name,
      password: form.password,
      role: form.role,
      is_active: form.is_active,
      is_superuser: form.is_superuser,
    });
  }
  ElMessage.success(t("saveSuccess"));
  dialogVisible.value = false;
  fetchUsers();
}

async function handleSearch() {
  query.page = 1;
  await fetchUsers();
}

async function handleReset() {
  query.keyword = "";
  query.page = 1;
  await fetchUsers();
}

async function handleToggle(row: UserRecord) {
  await toggleUserActive(row.id);
  ElMessage.success(t("toggleSuccess"));
  fetchUsers();
}

async function handleResetPassword(row: UserRecord) {
  const result = await ElMessageBox.prompt(t("resetPasswordPrompt"), t("resetPassword"), {
    inputType: "password",
    inputValidator: (value) => Boolean(value && value.length >= 6),
    inputErrorMessage: t("passwordMin"),
  });
  await resetUserPassword(row.id, result.value);
  ElMessage.success(t("resetPasswordSuccess"));
}

async function handleDelete(row: UserRecord) {
  await ElMessageBox.confirm(t("deleteConfirm"), t("delete"), { type: "warning" });
  await deleteUser(row.id);
  ElMessage.success(t("deleteSuccess"));
  fetchUsers();
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

onMounted(fetchUsers);
</script>

<template>
  <section class="management-page">
    <el-alert v-if="!canManage" type="warning" :title="t('permissionDenied')" show-icon />

    <template v-else>
      <div class="table-toolbar">
        <el-input v-model="query.keyword" :placeholder="t('keywordPlaceholder')" clearable @keyup.enter="handleSearch" />
        <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
        <el-button @click="handleReset">{{ t("reset") }}</el-button>
        <el-button type="success" @click="openCreateDialog">{{ t("addUser") }}</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" border class="data-table">
        <el-table-column prop="username" :label="t('username')" min-width="130" />
        <el-table-column prop="display_name" :label="t('displayName')" min-width="140" />
        <el-table-column prop="role" :label="t('role')" width="120">
          <template #default="{ row }">{{ row.is_superuser ? t("superuser") : t("staff") }}</template>
        </el-table-column>
        <el-table-column prop="is_superuser" :label="t('isSuperuser')" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'danger' : 'info'">{{ row.is_superuser ? t("superuser") : t("staff") }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" :label="t('isActive')" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? t("enabled") : t("disabled") }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('lastLoginAt')" min-width="170">
          <template #default="{ row }">{{ formatDate(row.last_login_at) }}</template>
        </el-table-column>
        <el-table-column :label="t('createdAt')" min-width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column :label="t('actions')" fixed="right" width="330">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">{{ t("edit") }}</el-button>
            <el-button size="small" @click="handleToggle(row)">{{ row.is_active ? t("disable") : t("enable") }}</el-button>
            <el-button size="small" @click="handleResetPassword(row)">{{ t("resetPassword") }}</el-button>
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
          @size-change="fetchUsers"
          @current-change="fetchUsers"
        />
      </div>

      <el-dialog v-model="dialogVisible" :title="dialogEditing ? t('editUser') : t('addUser')" width="520px">
        <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
          <el-form-item :label="t('username')" prop="username">
            <el-input v-model="form.username" :disabled="dialogEditing" />
          </el-form-item>
          <el-form-item :label="t('displayName')" prop="display_name">
            <el-input v-model="form.display_name" />
          </el-form-item>
          <el-form-item v-if="!dialogEditing" :label="t('password')" prop="password">
            <el-input v-model="form.password" type="password" show-password />
          </el-form-item>
          <el-form-item :label="t('role')">
            <el-input v-model="form.role" />
          </el-form-item>
          <el-form-item :label="t('isSuperuser')">
            <el-switch v-model="form.is_superuser" />
          </el-form-item>
          <el-form-item :label="t('isActive')">
            <el-switch v-model="form.is_active" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">{{ t("cancel") }}</el-button>
          <el-button type="primary" @click="saveUser">{{ t("confirm") }}</el-button>
        </template>
      </el-dialog>
    </template>
  </section>
</template>
