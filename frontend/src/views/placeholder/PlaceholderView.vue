<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { MessageKey, t } from "@/i18n";

const route = useRoute();
const title = computed(() => t((route.meta.titleKey as MessageKey) || "dashboard"));
</script>

<template>
  <section class="page-card">
    <h1>{{ title }}</h1>
    <p>{{ t("openModuleLater") }}</p>
  </section>
</template>
