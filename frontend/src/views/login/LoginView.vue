<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";

import { t } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  username: "admin",
  password: "admin123456",
});

const rules: FormRules = {
  username: [{ required: true, message: t("usernameRequired"), trigger: "blur" }],
  password: [{ required: true, message: t("passwordRequired"), trigger: "blur" }],
};

async function handleLogin() {
  await formRef.value?.validate();
  loading.value = true;
  try {
    await authStore.login(form.username, form.password);
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    router.push(redirect.startsWith("/login") ? "/" : redirect);
  } catch {
    ElMessage.error(t("loginFailed"));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-copy">
        <div class="login-logo">M</div>
        <h1>{{ t("appName") }}</h1>
        <p>{{ t("loginTip") }}</p>
      </div>

      <el-form ref="formRef" class="login-form" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <h2>{{ t("loginTitle") }}</h2>
        <el-form-item :label="t('username')">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="t('password')">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" class="login-submit" :loading="loading">
          {{ t("loginButton") }}
        </el-button>
      </el-form>
    </section>
  </main>
</template>
