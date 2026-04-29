<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";

import { t } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: "admin",
  password: "admin",
});

function handleLogin() {
  authStore.login(form.username);
  router.push("/");
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

      <el-form class="login-form" :model="form" label-position="top" @submit.prevent="handleLogin">
        <h2>{{ t("loginTitle") }}</h2>
        <el-form-item :label="t('username')">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="t('password')">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" class="login-submit">
          {{ t("loginButton") }}
        </el-button>
      </el-form>
    </section>
  </main>
</template>
