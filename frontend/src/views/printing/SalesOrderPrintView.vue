<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { getSalesOrderPrintData, updatePrintSetting } from "@/api/printing";
import { t } from "@/i18n";
import type { PrintSettingPayload, SalesOrderPrintData } from "@/types/printing";
import PrintSettingsDialog from "@/views/printing/components/PrintSettingsDialog.vue";

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const data = ref<SalesOrderPrintData | null>(null);
const settingsVisible = ref(false);

const settings = computed(() => data.value?.print_settings ?? null);
const showCancelled = computed(() => data.value?.status === "cancelled");

function money(value?: string | null) {
  return Number(value ?? 0).toFixed(2);
}

function qty(value?: string | null) {
  return Number(value ?? 0).toFixed(3);
}

function statusText(status: string) {
  const map: Record<string, string> = {
    draft: t("salesStatusDraft"),
    confirmed: t("salesStatusConfirmed"),
    cancelled: t("salesStatusCancelled"),
  };
  return map[status] ?? status;
}

function specText(item: { product_spec: string | null; product_model: string | null }) {
  return [item.product_spec, item.product_model].filter(Boolean).join(" / ");
}

async function fetchData() {
  loading.value = true;
  try {
    const id = Number(route.params.id);
    const response = await getSalesOrderPrintData(id);
    data.value = response.data;
  } finally {
    loading.value = false;
  }
}

async function saveSettings(payload: PrintSettingPayload) {
  await updatePrintSetting("sales_order", payload);
  ElMessage.success(t("saveSuccess"));
  settingsVisible.value = false;
  await fetchData();
}

function printPage() {
  window.print();
}

onMounted(fetchData);
</script>

<template>
  <section class="print-page" v-loading="loading">
    <div class="print-toolbar">
      <el-button @click="router.back()">{{ t("back") }}</el-button>
      <el-button @click="settingsVisible = true">{{ t("printSettings") }}</el-button>
      <el-button type="primary" @click="printPage">{{ t("print") }}</el-button>
    </div>

    <article v-if="data" class="print-sheet">
      <div v-if="showCancelled" class="void-watermark">{{ t("cancelledWatermark") }}</div>
      <header class="print-header">
        <p v-if="settings?.show_company_name && settings.company_name" class="company-name">{{ settings.company_name }}</p>
        <h1>{{ t("salesOrderPrintTitle") }}</h1>
        <p v-if="settings?.show_contact && settings.contact_text" class="contact-text">{{ settings.contact_text }}</p>
      </header>

      <div class="print-meta">
        <span>{{ t("salesOrderNo") }}：{{ data.order_no }}</span>
        <span>{{ t("salesDate") }}：{{ data.order_date }}</span>
        <span>{{ t("salesStatus") }}：{{ statusText(data.status) }}</span>
        <span>{{ t("customerName") }}：{{ data.customer_name }}</span>
        <span>{{ t("phone") }}：{{ data.customer_phone || "-" }}</span>
        <span>{{ t("address") }}：{{ data.customer_address || "-" }}</span>
        <span>{{ t("warehouse") }}：{{ data.warehouse_name }}</span>
        <span>{{ t("operator") }}：{{ data.created_by_name || "-" }}</span>
      </div>

      <table class="print-table">
        <thead>
          <tr>
            <th>{{ t("sequence") }}</th>
            <th>{{ t("productCode") }}</th>
            <th>{{ t("productName") }}</th>
            <th>{{ t("productSpecModel") }}</th>
            <th>{{ t("productUnit") }}</th>
            <th>{{ t("quantity") }}</th>
            <th v-if="settings?.show_unit_price">{{ t("unitPrice") }}</th>
            <th v-if="settings?.show_discount">{{ t("lineDiscount") }}</th>
            <th v-if="settings?.show_amount">{{ t("amount") }}</th>
            <th v-if="settings?.show_remark">{{ t("remark") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in data.items" :key="item.id">
            <td>{{ index + 1 }}</td>
            <td>{{ item.product_code || "-" }}</td>
            <td>{{ item.product_name }}</td>
            <td>{{ specText(item) || "-" }}</td>
            <td>{{ item.unit_name || "-" }}</td>
            <td class="number-cell">{{ qty(item.quantity) }}</td>
            <td v-if="settings?.show_unit_price" class="number-cell">{{ money(item.unit_price) }}</td>
            <td v-if="settings?.show_discount" class="number-cell">{{ money(item.discount_amount) }}</td>
            <td v-if="settings?.show_amount" class="number-cell">{{ money(item.line_amount) }}</td>
            <td v-if="settings?.show_remark">{{ item.remark || "-" }}</td>
          </tr>
        </tbody>
      </table>

      <div class="print-summary">
        <span>{{ t("totalQuantity") }}：{{ qty(data.total_quantity) }}</span>
        <span>{{ t("totalAmount") }}：{{ money(data.total_amount) }}</span>
        <span>{{ t("orderDiscount") }}：{{ money(data.discount_amount) }}</span>
        <span>{{ t("receivableAmount") }}：{{ money(data.receivable_amount) }}</span>
        <span>{{ t("paidAmount") }}：{{ money(data.paid_amount) }}</span>
        <span>{{ t("unpaidAmount") }}：{{ money(data.unpaid_amount) }}</span>
      </div>

      <p v-if="settings?.show_remark" class="print-remark">{{ t("remark") }}：{{ data.remark || "-" }}</p>
      <p v-if="settings?.footer_text" class="print-footer-text">{{ settings.footer_text }}</p>
      <div v-if="settings?.show_signature" class="signature-row">
        <span>{{ t("preparedBy") }}：</span>
        <span>{{ t("confirmedAt") }}：</span>
        <span>{{ t("customerSignature") }}：</span>
      </div>
    </article>

    <PrintSettingsDialog v-model="settingsVisible" :setting="settings" @save="saveSettings" />
  </section>
</template>

