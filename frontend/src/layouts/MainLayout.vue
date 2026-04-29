<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { moduleRoutes } from "@/router";
import { useAuthStore } from "@/stores/auth";
import { MessageKey, t } from "@/i18n";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const activePath = computed(() => route.path);

const menuItems = computed(() => [
  { path: "/", title: t("dashboard") },
  ...moduleRoutes.map((item) => ({
    path: `/${item.path}`,
    title: t(item.titleKey as MessageKey),
  })),
]);

async function handleLogout() {
  await authStore.logout();
  router.push("/login");
}
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="app-sidebar">
      <div class="brand">
        <div class="brand-mark">M</div>
        <div>
          <div class="brand-title">{{ t("appName") }}</div>
          <div class="brand-subtitle">{{ t("appSubtitle") }}</div>
        </div>
      </div>

      <el-menu :default-active="activePath" router class="side-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="page-title">{{ route.meta.titleKey ? t(route.meta.titleKey as MessageKey) : t("dashboard") }}</div>
        <div class="header-actions">
          <span class="user-name">{{ authStore.displayName || "admin" }}</span>
          <el-button @click="handleLogout">{{ t("logout") }}</el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>
