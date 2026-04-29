<script setup lang="ts">
import { ref } from "vue";

import { getHealth } from "@/api/health";
import { t } from "@/i18n";

const healthText = ref("");

async function checkHealth() {
  const response = await getHealth();
  healthText.value = `${response.data.service}: ${response.data.status}`;
}
</script>

<template>
  <section class="page-card">
    <h1>{{ t("scaffoldReady") }}</h1>
    <p>{{ t("scaffoldIntro") }}</p>
    <el-button type="primary" @click="checkHealth">{{ t("backendHealth") }}</el-button>
    <p v-if="healthText" class="health-result">{{ healthText }}</p>
  </section>
</template>
