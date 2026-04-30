<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import {
  getFinanceByCategory,
  getFinanceSummary,
  getInventoryMovementSummary,
  getInventorySummary,
  getPayables,
  getProfitReport,
  getPurchaseByProduct,
  getPurchaseBySupplier,
  getPurchaseSummary,
  getReceivables,
  getReportOverview,
  getSalesByCustomer,
  getSalesByProduct,
  getSalesSummary,
} from "@/api/reports";
import { t } from "@/i18n";
import type {
  FinanceByCategoryItem,
  FinanceSummary,
  InventoryMovementSummary,
  InventorySummary,
  OverviewReport,
  PayableItem,
  ProfitSummary,
  PurchaseByProductItem,
  PurchaseBySupplierItem,
  PurchaseSummary,
  ReceivableItem,
  SalesByCustomerItem,
  SalesByProductItem,
  SalesSummary,
} from "@/types/report";

const activeTab = ref("overview");
const loading = ref(false);
const overview = ref<OverviewReport | null>(null);
const salesSummary = ref<SalesSummary | null>(null);
const purchaseSummary = ref<PurchaseSummary | null>(null);
const inventorySummary = ref<InventorySummary | null>(null);
const movementSummary = ref<InventoryMovementSummary | null>(null);
const financeSummary = ref<FinanceSummary | null>(null);
const profitSummary = ref<ProfitSummary | null>(null);
const salesByCustomer = ref<SalesByCustomerItem[]>([]);
const salesByProduct = ref<SalesByProductItem[]>([]);
const purchaseBySupplier = ref<PurchaseBySupplierItem[]>([]);
const purchaseByProduct = ref<PurchaseByProductItem[]>([]);
const receivables = ref<ReceivableItem[]>([]);
const payables = ref<PayableItem[]>([]);
const financeByCategory = ref<FinanceByCategoryItem[]>([]);

const query = reactive({
  dateRange: [] as string[],
  keyword: "",
  includeZero: false,
});

const dateParams = computed(() => ({
  start_date: query.dateRange[0],
  end_date: query.dateRange[1],
}));

function currentMonthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
  const end = now.toISOString().slice(0, 10);
  return [start, end];
}

function money(value?: string) {
  return Number(value || 0).toFixed(2);
}

function qty(value?: string) {
  return Number(value || 0).toFixed(3);
}

function movementTypeText(value: string) {
  const key = `movementType_${value}` as Parameters<typeof t>[0];
  return t(key) || value;
}

function financeTypeText(value: string) {
  return value === "income" ? t("financeIncome") : t("financeExpense");
}

async function fetchReports() {
  loading.value = true;
  try {
    const [
      overviewResponse,
      salesResponse,
      salesCustomerResponse,
      salesProductResponse,
      purchaseResponse,
      purchaseSupplierResponse,
      purchaseProductResponse,
      receivableResponse,
      payableResponse,
      inventoryResponse,
      movementResponse,
      financeResponse,
      financeCategoryResponse,
      profitResponse,
    ] = await Promise.all([
      getReportOverview(dateParams.value),
      getSalesSummary(dateParams.value),
      getSalesByCustomer({ ...dateParams.value, page: 1, page_size: 20 }),
      getSalesByProduct({ ...dateParams.value, page: 1, page_size: 20 }),
      getPurchaseSummary(dateParams.value),
      getPurchaseBySupplier({ ...dateParams.value, page: 1, page_size: 20 }),
      getPurchaseByProduct({ ...dateParams.value, page: 1, page_size: 20 }),
      getReceivables({ keyword: query.keyword || undefined, include_zero: query.includeZero, page: 1, page_size: 20 }),
      getPayables({ keyword: query.keyword || undefined, include_zero: query.includeZero, page: 1, page_size: 20 }),
      getInventorySummary(),
      getInventoryMovementSummary(dateParams.value),
      getFinanceSummary(dateParams.value),
      getFinanceByCategory({ ...dateParams.value, page: 1, page_size: 20 }),
      getProfitReport(dateParams.value),
    ]);
    overview.value = overviewResponse.data;
    salesSummary.value = salesResponse.data;
    salesByCustomer.value = salesCustomerResponse.data.items;
    salesByProduct.value = salesProductResponse.data.items;
    purchaseSummary.value = purchaseResponse.data;
    purchaseBySupplier.value = purchaseSupplierResponse.data.items;
    purchaseByProduct.value = purchaseProductResponse.data.items;
    receivables.value = receivableResponse.data.items;
    payables.value = payableResponse.data.items;
    inventorySummary.value = inventoryResponse.data;
    movementSummary.value = movementResponse.data;
    financeSummary.value = financeResponse.data;
    financeByCategory.value = financeCategoryResponse.data.items;
    profitSummary.value = profitResponse.data;
  } finally {
    loading.value = false;
  }
}

function handleReset() {
  query.dateRange = currentMonthRange();
  query.keyword = "";
  query.includeZero = false;
  fetchReports();
}

onMounted(() => {
  query.dateRange = currentMonthRange();
  fetchReports();
});
</script>

<template>
  <section class="management-page reports-page">
    <div class="table-toolbar reports-toolbar">
      <el-date-picker v-model="query.dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('startDate')" :end-placeholder="t('endDate')" />
      <el-input v-model="query.keyword" :placeholder="t('reportCounterpartyKeyword')" clearable @keyup.enter="fetchReports" />
      <el-checkbox v-model="query.includeZero">{{ t("reportIncludeZero") }}</el-checkbox>
      <el-button type="primary" @click="fetchReports">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
    </div>

    <el-tabs v-model="activeTab" v-loading="loading">
      <el-tab-pane :label="t('reportOverview')" name="overview">
        <div class="report-card-grid">
          <div class="report-card"><span>{{ t("reportSalesAmount") }}</span><strong>{{ money(overview?.sales_summary.receivable_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportPurchaseAmount") }}</span><strong>{{ money(overview?.purchase_summary.payable_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportReceivableTotal") }}</span><strong>{{ money(overview?.receivable_summary.total_receivable) }}</strong></div>
          <div class="report-card"><span>{{ t("reportPayableTotal") }}</span><strong>{{ money(overview?.payable_summary.total_payable) }}</strong></div>
          <div class="report-card"><span>{{ t("reportInventoryAmount") }}</span><strong>{{ money(overview?.inventory_summary.total_cost) }}</strong></div>
          <div class="report-card"><span>{{ t("reportAccountBalance") }}</span><strong>{{ money(overview?.finance_summary.balance_total) }}</strong></div>
          <div class="report-card"><span>{{ t("reportFinanceNet") }}</span><strong>{{ money(overview?.finance_summary.net_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportEstimatedProfit") }}</span><strong>{{ money(overview?.profit_summary.estimated_net_profit) }}</strong></div>
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('salesReport')" name="sales">
        <div class="report-card-grid">
          <div class="report-card"><span>{{ t("salesOrders") }}</span><strong>{{ salesSummary?.order_count || 0 }}</strong></div>
          <div class="report-card"><span>{{ t("totalQuantity") }}</span><strong>{{ qty(salesSummary?.total_quantity) }}</strong></div>
          <div class="report-card"><span>{{ t("receivableAmount") }}</span><strong>{{ money(salesSummary?.receivable_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("paidAmount") }}</span><strong>{{ money(salesSummary?.paid_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("unpaidAmount") }}</span><strong>{{ money(salesSummary?.unpaid_amount) }}</strong></div>
        </div>
        <h3>{{ t("reportByCustomer") }}</h3>
        <el-table :data="salesByCustomer" border :empty-text="t('noData')">
          <el-table-column prop="customer_name" :label="t('customerName')" />
          <el-table-column prop="order_count" :label="t('salesOrders')" />
          <el-table-column prop="sales_amount" :label="t('reportSalesAmount')" align="right" />
          <el-table-column prop="paid_amount" :label="t('paidAmount')" align="right" />
          <el-table-column prop="unpaid_amount" :label="t('unpaidAmount')" align="right" />
        </el-table>
        <h3>{{ t("reportByProduct") }}</h3>
        <el-table :data="salesByProduct" border :empty-text="t('noData')">
          <el-table-column prop="product_code" :label="t('productCode')" />
          <el-table-column prop="product_name" :label="t('productName')" />
          <el-table-column prop="quantity" :label="t('quantity')" align="right" />
          <el-table-column prop="sales_amount" :label="t('reportSalesAmount')" align="right" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('purchaseReport')" name="purchase">
        <div class="report-card-grid">
          <div class="report-card"><span>{{ t("purchaseOrders") }}</span><strong>{{ purchaseSummary?.order_count || 0 }}</strong></div>
          <div class="report-card"><span>{{ t("totalQuantity") }}</span><strong>{{ qty(purchaseSummary?.total_quantity) }}</strong></div>
          <div class="report-card"><span>{{ t("payableAmount") }}</span><strong>{{ money(purchaseSummary?.payable_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("paidAmount") }}</span><strong>{{ money(purchaseSummary?.paid_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("unpaidAmount") }}</span><strong>{{ money(purchaseSummary?.unpaid_amount) }}</strong></div>
        </div>
        <h3>{{ t("reportBySupplier") }}</h3>
        <el-table :data="purchaseBySupplier" border :empty-text="t('noData')">
          <el-table-column prop="supplier_name" :label="t('supplierName')" />
          <el-table-column prop="order_count" :label="t('purchaseOrders')" />
          <el-table-column prop="purchase_amount" :label="t('reportPurchaseAmount')" align="right" />
          <el-table-column prop="paid_amount" :label="t('paidAmount')" align="right" />
          <el-table-column prop="unpaid_amount" :label="t('unpaidAmount')" align="right" />
        </el-table>
        <h3>{{ t("reportByProduct") }}</h3>
        <el-table :data="purchaseByProduct" border :empty-text="t('noData')">
          <el-table-column prop="product_code" :label="t('productCode')" />
          <el-table-column prop="product_name" :label="t('productName')" />
          <el-table-column prop="quantity" :label="t('quantity')" align="right" />
          <el-table-column prop="purchase_amount" :label="t('reportPurchaseAmount')" align="right" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('receivablePayableReport')" name="receivable">
        <h3>{{ t("reportReceivables") }}</h3>
        <el-table :data="receivables" border :empty-text="t('noData')">
          <el-table-column prop="customer_code" :label="t('customerCode')" />
          <el-table-column prop="customer_name" :label="t('customerName')" />
          <el-table-column prop="phone" :label="t('phone')" />
          <el-table-column prop="current_receivable" :label="t('currentReceivable')" align="right" />
        </el-table>
        <h3>{{ t("reportPayables") }}</h3>
        <el-table :data="payables" border :empty-text="t('noData')">
          <el-table-column prop="supplier_code" :label="t('supplierCode')" />
          <el-table-column prop="supplier_name" :label="t('supplierName')" />
          <el-table-column prop="phone" :label="t('phone')" />
          <el-table-column prop="current_payable" :label="t('currentPayable')" align="right" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('inventoryReport')" name="inventory">
        <div class="report-card-grid">
          <div class="report-card"><span>{{ t("products") }}</span><strong>{{ inventorySummary?.product_count || 0 }}</strong></div>
          <div class="report-card"><span>{{ t("quantityOnHand") }}</span><strong>{{ qty(inventorySummary?.total_quantity) }}</strong></div>
          <div class="report-card"><span>{{ t("inventoryAmount") }}</span><strong>{{ money(inventorySummary?.total_cost) }}</strong></div>
          <div class="report-card"><span>{{ t("lowStock") }}</span><strong>{{ inventorySummary?.low_stock_count || 0 }}</strong></div>
          <div class="report-card"><span>{{ t("stockIn") }}</span><strong>{{ qty(movementSummary?.in_quantity) }}</strong></div>
          <div class="report-card"><span>{{ t("stockOut") }}</span><strong>{{ qty(movementSummary?.out_quantity) }}</strong></div>
        </div>
        <el-table :data="movementSummary?.items || []" border :empty-text="t('noData')">
          <el-table-column :label="t('movementType')">
            <template #default="{ row }">{{ movementTypeText(row.movement_type) }}</template>
          </el-table-column>
          <el-table-column :label="t('direction')">
            <template #default="{ row }">{{ row.direction === "in" ? t("stockIn") : t("stockOut") }}</template>
          </el-table-column>
          <el-table-column prop="quantity" :label="t('quantity')" align="right" />
          <el-table-column prop="amount" :label="t('amount')" align="right" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('financeReport')" name="finance">
        <div class="report-card-grid">
          <div class="report-card"><span>{{ t("financeAccounts") }}</span><strong>{{ financeSummary?.account_count || 0 }}</strong></div>
          <div class="report-card"><span>{{ t("reportAccountBalance") }}</span><strong>{{ money(financeSummary?.balance_total) }}</strong></div>
          <div class="report-card"><span>{{ t("financeIncome") }}</span><strong>{{ money(financeSummary?.income_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("financeExpense") }}</span><strong>{{ money(financeSummary?.expense_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportFinanceNet") }}</span><strong>{{ money(financeSummary?.net_amount) }}</strong></div>
        </div>
        <h3>{{ t("financeAccounts") }}</h3>
        <el-table :data="financeSummary?.accounts || []" border :empty-text="t('noData')">
          <el-table-column prop="account_name" :label="t('financeAccountName')" />
          <el-table-column prop="opening_balance" :label="t('openingBalance')" align="right" />
          <el-table-column prop="current_balance" :label="t('currentBalance')" align="right" />
        </el-table>
        <h3>{{ t("reportByCategory") }}</h3>
        <el-table :data="financeByCategory" border :empty-text="t('noData')">
          <el-table-column prop="category_name" :label="t('financeCategory')" />
          <el-table-column :label="t('financeType')">
            <template #default="{ row }">{{ financeTypeText(row.type) }}</template>
          </el-table-column>
          <el-table-column prop="amount" :label="t('amount')" align="right" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('profitReport')" name="profit">
        <el-alert :title="t('profitEstimateNotice')" type="warning" show-icon :closable="false" />
        <div class="report-card-grid report-profit-grid">
          <div class="report-card"><span>{{ t("reportSalesAmount") }}</span><strong>{{ money(profitSummary?.sales_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportPurchaseAmount") }}</span><strong>{{ money(profitSummary?.purchase_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportGrossProfit") }}</span><strong>{{ money(profitSummary?.gross_profit) }}</strong></div>
          <div class="report-card"><span>{{ t("financeIncome") }}</span><strong>{{ money(profitSummary?.income_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("financeExpense") }}</span><strong>{{ money(profitSummary?.expense_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportFinanceNet") }}</span><strong>{{ money(profitSummary?.finance_net_amount) }}</strong></div>
          <div class="report-card"><span>{{ t("reportEstimatedProfit") }}</span><strong>{{ money(profitSummary?.estimated_net_profit) }}</strong></div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>
