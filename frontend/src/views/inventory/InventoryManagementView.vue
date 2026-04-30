<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";

import { listProductCategories } from "@/api/products";
import {
  adjustInventory,
  listInventory,
  listStockMovements,
  listWarehouses,
  setInitialStock,
} from "@/api/inventory";
import { t } from "@/i18n";
import type { ProductCategory } from "@/types/product";
import type { InventoryRecord, StockMovementRecord, Warehouse } from "@/types/inventory";

const activeTab = ref<"balance" | "movements">("balance");
const balanceLoading = ref(false);
const movementLoading = ref(false);
const warehouses = ref<Warehouse[]>([]);
const categories = ref<ProductCategory[]>([]);
const balanceRows = ref<InventoryRecord[]>([]);
const movementRows = ref<StockMovementRecord[]>([]);
const balanceTotal = ref(0);
const movementTotal = ref(0);
const initialDialogVisible = ref(false);
const adjustmentDialogVisible = ref(false);
const currentRow = ref<InventoryRecord | null>(null);
const initialFormRef = ref<FormInstance>();
const adjustmentFormRef = ref<FormInstance>();

const balanceQuery = reactive({
  keyword: "",
  categoryId: undefined as number | undefined,
  warehouseId: undefined as number | undefined,
  lowStockOnly: false,
  page: 1,
  pageSize: 10,
});

const movementQuery = reactive({
  keyword: "",
  warehouseId: undefined as number | undefined,
  movementType: "",
  direction: "",
  dateRange: [] as string[],
  productId: undefined as number | undefined,
  page: 1,
  pageSize: 10,
});

const initialForm = reactive({
  warehouse_id: undefined as number | undefined,
  quantity: 0,
  unit_cost: 0,
  remark: "",
});

const adjustmentForm = reactive({
  warehouse_id: undefined as number | undefined,
  mode: "increase" as "increase" | "decrease" | "set",
  quantity: 0,
  target_qty: 0,
  unit_cost: 0,
  remark: "",
});

const initialRules: FormRules = {
  quantity: [{ required: true, message: t("initialQtyRequired"), trigger: "blur" }],
  unit_cost: [{ required: true, message: t("unitCostRequired"), trigger: "blur" }],
};

const adjustmentRules: FormRules = {
  mode: [{ required: true, message: t("adjustModeRequired"), trigger: "change" }],
};

const defaultWarehouseId = computed(() => warehouses.value.find((item) => item.is_default)?.id);

const movementTypeOptions = [
  "initial",
  "adjustment_in",
  "adjustment_out",
  "stocktaking_gain",
  "stocktaking_loss",
  "purchase_in",
  "sale_out",
  "cancel_reverse",
];

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function qty(value: number) {
  return value.toFixed(3);
}

function cost(value: number) {
  return value.toFixed(4);
}

function movementTypeText(value: string) {
  const typeMap: Record<string, string> = {
    initial: t("movementType_initial"),
    adjustment_in: t("movementType_adjustment_in"),
    adjustment_out: t("movementType_adjustment_out"),
    stocktaking_gain: t("movementType_stocktaking_gain"),
    stocktaking_loss: t("movementType_stocktaking_loss"),
    purchase_in: t("movementType_purchase_in"),
    sale_out: t("movementType_sale_out"),
    cancel_reverse: t("movementType_cancel_reverse"),
  };
  return typeMap[value] || value;
}

function movementSourceText(value: string) {
  const key = `sourceType_${value}`;
  const sourceMap: Record<string, string> = {
    sourceType_manual_initial: t("sourceType_manual_initial"),
    sourceType_manual_adjustment: t("sourceType_manual_adjustment"),
    sourceType_stocktaking: t("sourceType_stocktaking"),
    sourceType_sales_order: t("sourceType_sales_order"),
    sourceType_purchase_order: t("sourceType_purchase_order"),
  };
  return sourceMap[key] || value;
}

async function fetchBaseData() {
  const [warehouseResponse, categoryResponse] = await Promise.all([listWarehouses(), listProductCategories()]);
  warehouses.value = warehouseResponse.data;
  categories.value = categoryResponse.data;
  if (!balanceQuery.warehouseId) {
    balanceQuery.warehouseId = defaultWarehouseId.value;
  }
}

async function fetchBalances() {
  balanceLoading.value = true;
  try {
    const response = await listInventory({
      keyword: balanceQuery.keyword || undefined,
      category_id: balanceQuery.categoryId,
      warehouse_id: balanceQuery.warehouseId,
      low_stock_only: balanceQuery.lowStockOnly,
      page: balanceQuery.page,
      page_size: balanceQuery.pageSize,
    });
    balanceRows.value = response.data.items;
    balanceTotal.value = response.data.total;
  } finally {
    balanceLoading.value = false;
  }
}

async function fetchMovements() {
  movementLoading.value = true;
  try {
    const response = await listStockMovements({
      keyword: movementQuery.keyword || undefined,
      product_id: movementQuery.productId,
      warehouse_id: movementQuery.warehouseId,
      movement_type: movementQuery.movementType || undefined,
      direction: movementQuery.direction || undefined,
      start_date: movementQuery.dateRange[0],
      end_date: movementQuery.dateRange[1],
      page: movementQuery.page,
      page_size: movementQuery.pageSize,
    });
    movementRows.value = response.data.items;
    movementTotal.value = response.data.total;
  } finally {
    movementLoading.value = false;
  }
}

async function searchBalances() {
  balanceQuery.page = 1;
  await fetchBalances();
}

async function resetBalances() {
  balanceQuery.keyword = "";
  balanceQuery.categoryId = undefined;
  balanceQuery.lowStockOnly = false;
  balanceQuery.page = 1;
  await fetchBalances();
}

async function searchMovements() {
  movementQuery.page = 1;
  await fetchMovements();
}

async function resetMovements() {
  movementQuery.keyword = "";
  movementQuery.warehouseId = undefined;
  movementQuery.movementType = "";
  movementQuery.direction = "";
  movementQuery.dateRange = [];
  movementQuery.productId = undefined;
  movementQuery.page = 1;
  await fetchMovements();
}

function openInitialDialog(row: InventoryRecord) {
  currentRow.value = row;
  initialForm.warehouse_id = row.warehouse_id || defaultWarehouseId.value;
  initialForm.quantity = 0;
  initialForm.unit_cost = 0;
  initialForm.remark = "";
  initialDialogVisible.value = true;
}

function openAdjustmentDialog(row: InventoryRecord) {
  currentRow.value = row;
  adjustmentForm.warehouse_id = row.warehouse_id || defaultWarehouseId.value;
  adjustmentForm.mode = "increase";
  adjustmentForm.quantity = 0;
  adjustmentForm.target_qty = Number(row.quantity_on_hand);
  adjustmentForm.unit_cost = 0;
  adjustmentForm.remark = "";
  adjustmentDialogVisible.value = true;
}

async function submitInitialStock() {
  await initialFormRef.value?.validate();
  if (!currentRow.value) {
    return;
  }
  await setInitialStock({
    product_id: currentRow.value.product_id,
    warehouse_id: initialForm.warehouse_id || null,
    quantity: qty(initialForm.quantity),
    unit_cost: cost(initialForm.unit_cost),
    remark: initialForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  initialDialogVisible.value = false;
  await Promise.all([fetchBalances(), fetchMovements()]);
}

async function submitAdjustment() {
  await adjustmentFormRef.value?.validate();
  if (!currentRow.value) {
    return;
  }
  if (adjustmentForm.mode !== "set" && adjustmentForm.quantity <= 0) {
    ElMessage.error(t("adjustQtyRequired"));
    return;
  }
  if (adjustmentForm.mode === "set" && adjustmentForm.target_qty < 0) {
    ElMessage.error(t("targetQtyInvalid"));
    return;
  }
  await adjustInventory({
    product_id: currentRow.value.product_id,
    warehouse_id: adjustmentForm.warehouse_id || null,
    mode: adjustmentForm.mode,
    quantity: adjustmentForm.mode === "set" ? null : qty(adjustmentForm.quantity),
    target_qty: adjustmentForm.mode === "set" ? qty(adjustmentForm.target_qty) : null,
    unit_cost: adjustmentForm.unit_cost >= 0 ? cost(adjustmentForm.unit_cost) : null,
    remark: adjustmentForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  adjustmentDialogVisible.value = false;
  await Promise.all([fetchBalances(), fetchMovements()]);
}

async function viewMovements(row: InventoryRecord) {
  activeTab.value = "movements";
  movementQuery.productId = row.product_id;
  movementQuery.warehouseId = row.warehouse_id;
  movementQuery.page = 1;
  await fetchMovements();
}

onMounted(async () => {
  await fetchBaseData();
  await Promise.all([fetchBalances(), fetchMovements()]);
});
</script>

<template>
  <section class="management-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane :label="t('inventoryBalance')" name="balance">
        <div class="table-toolbar inventory-toolbar">
          <el-input v-model="balanceQuery.keyword" :placeholder="t('inventoryKeywordPlaceholder')" clearable @keyup.enter="searchBalances" />
          <el-select v-model="balanceQuery.categoryId" :placeholder="t('productCategory')" clearable>
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-select v-model="balanceQuery.warehouseId" :placeholder="t('warehouse')" clearable>
            <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-checkbox v-model="balanceQuery.lowStockOnly">{{ t("lowStockOnly") }}</el-checkbox>
          <el-button type="primary" @click="searchBalances">{{ t("search") }}</el-button>
          <el-button @click="resetBalances">{{ t("reset") }}</el-button>
        </div>

        <el-table v-loading="balanceLoading" :data="balanceRows" border class="data-table" :empty-text="t('noData')">
          <el-table-column prop="product_code" :label="t('productCode')" min-width="120" />
          <el-table-column prop="barcode" :label="t('productBarcode')" min-width="130" />
          <el-table-column prop="product_name" :label="t('productName')" min-width="150" />
          <el-table-column prop="category_name" :label="t('productCategory')" min-width="110" />
          <el-table-column prop="unit_name" :label="t('productUnit')" min-width="90" />
          <el-table-column prop="spec" :label="t('productSpec')" min-width="100" />
          <el-table-column prop="model" :label="t('productModel')" min-width="100" />
          <el-table-column prop="warehouse_name" :label="t('warehouse')" min-width="110" />
          <el-table-column prop="quantity_on_hand" :label="t('quantityOnHand')" min-width="110" align="right" />
          <el-table-column prop="average_cost" :label="t('averageCost')" min-width="110" align="right" />
          <el-table-column prop="total_cost" :label="t('inventoryAmount')" min-width="110" align="right" />
          <el-table-column prop="stock_warning_qty" :label="t('stockWarningQty')" min-width="110" align="right" />
          <el-table-column :label="t('warningStatus')" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.is_low_stock" type="danger">{{ t("lowStock") }}</el-tag>
              <el-tag v-else type="success">{{ t("normalStock") }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('updatedAt')" min-width="170">
            <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column :label="t('actions')" fixed="right" width="260">
            <template #default="{ row }">
              <el-button size="small" @click="openInitialDialog(row)">{{ t("initialStock") }}</el-button>
              <el-button size="small" @click="openAdjustmentDialog(row)">{{ t("inventoryAdjustment") }}</el-button>
              <el-button size="small" @click="viewMovements(row)">{{ t("viewMovements") }}</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="balanceQuery.page"
            v-model:page-size="balanceQuery.pageSize"
            :total="balanceTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchBalances"
            @current-change="fetchBalances"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('stockMovements')" name="movements">
        <div class="table-toolbar inventory-toolbar">
          <el-input v-model="movementQuery.keyword" :placeholder="t('movementKeywordPlaceholder')" clearable @keyup.enter="searchMovements" />
          <el-select v-model="movementQuery.warehouseId" :placeholder="t('warehouse')" clearable>
            <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-select v-model="movementQuery.movementType" :placeholder="t('movementType')" clearable>
            <el-option v-for="item in movementTypeOptions" :key="item" :label="movementTypeText(item)" :value="item" />
          </el-select>
          <el-select v-model="movementQuery.direction" :placeholder="t('direction')" clearable>
            <el-option :label="t('stockIn')" value="in" />
            <el-option :label="t('stockOut')" value="out" />
          </el-select>
          <el-date-picker v-model="movementQuery.dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('startDate')" :end-placeholder="t('endDate')" />
          <el-button type="primary" @click="searchMovements">{{ t("search") }}</el-button>
          <el-button @click="resetMovements">{{ t("reset") }}</el-button>
        </div>

        <el-table v-loading="movementLoading" :data="movementRows" border class="data-table" :empty-text="t('noData')">
          <el-table-column prop="movement_no" :label="t('movementNo')" min-width="150" />
          <el-table-column :label="t('date')" min-width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="product_code" :label="t('productCode')" min-width="120" />
          <el-table-column prop="product_name" :label="t('productName')" min-width="150" />
          <el-table-column prop="warehouse_name" :label="t('warehouse')" min-width="110" />
          <el-table-column :label="t('movementType')" min-width="120">
            <template #default="{ row }">{{ movementTypeText(row.movement_type) }}</template>
          </el-table-column>
          <el-table-column :label="t('direction')" width="90">
            <template #default="{ row }">
              <el-tag :type="row.direction === 'in' ? 'success' : 'warning'">{{ row.direction === "in" ? t("stockIn") : t("stockOut") }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" :label="t('quantity')" min-width="100" align="right" />
          <el-table-column prop="unit_cost" :label="t('unitCost')" min-width="110" align="right" />
          <el-table-column prop="amount" :label="t('amount')" min-width="110" align="right" />
          <el-table-column prop="before_qty" :label="t('beforeQty')" min-width="110" align="right" />
          <el-table-column prop="after_qty" :label="t('afterQty')" min-width="110" align="right" />
          <el-table-column :label="t('sourceType')" min-width="120">
            <template #default="{ row }">{{ movementSourceText(row.source_type) }}</template>
          </el-table-column>
          <el-table-column prop="remark" :label="t('remark')" min-width="160" show-overflow-tooltip />
          <el-table-column prop="created_by_name" :label="t('operator')" min-width="110" />
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="movementQuery.page"
            v-model:page-size="movementQuery.pageSize"
            :total="movementTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchMovements"
            @current-change="fetchMovements"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="initialDialogVisible" :title="t('initialStock')" width="520px">
      <el-form ref="initialFormRef" :model="initialForm" :rules="initialRules" label-width="110px">
        <el-form-item :label="t('productName')">
          <el-input :model-value="currentRow?.product_name" disabled />
        </el-form-item>
        <el-form-item :label="t('warehouse')">
          <el-select v-model="initialForm.warehouse_id" class="form-wide-control">
            <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('initialQuantity')" prop="quantity">
          <el-input-number v-model="initialForm.quantity" :min="0" :precision="3" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('unitCost')" prop="unit_cost">
          <el-input-number v-model="initialForm.unit_cost" :min="0" :precision="4" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="initialForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="initialDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitInitialStock">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="adjustmentDialogVisible" :title="t('inventoryAdjustment')" width="560px">
      <el-form ref="adjustmentFormRef" :model="adjustmentForm" :rules="adjustmentRules" label-width="120px">
        <el-form-item :label="t('productName')">
          <el-input :model-value="currentRow?.product_name" disabled />
        </el-form-item>
        <el-form-item :label="t('quantityOnHand')">
          <el-input :model-value="currentRow?.quantity_on_hand" disabled />
        </el-form-item>
        <el-form-item :label="t('warehouse')">
          <el-select v-model="adjustmentForm.warehouse_id" class="form-wide-control">
            <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('adjustMode')" prop="mode">
          <el-radio-group v-model="adjustmentForm.mode">
            <el-radio-button label="increase">{{ t("increaseStock") }}</el-radio-button>
            <el-radio-button label="decrease">{{ t("decreaseStock") }}</el-radio-button>
            <el-radio-button label="set">{{ t("setStock") }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="adjustmentForm.mode !== 'set'" :label="t('adjustQuantity')">
          <el-input-number v-model="adjustmentForm.quantity" :min="0" :precision="3" class="form-wide-control" />
        </el-form-item>
        <el-form-item v-else :label="t('targetQuantity')">
          <el-input-number v-model="adjustmentForm.target_qty" :min="0" :precision="3" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('unitCost')">
          <el-input-number v-model="adjustmentForm.unit_cost" :min="0" :precision="4" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="adjustmentForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustmentDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitAdjustment">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>
  </section>
</template>
