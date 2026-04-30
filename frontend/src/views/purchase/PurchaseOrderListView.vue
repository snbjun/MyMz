<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { useRouter } from "vue-router";

import { listSuppliers } from "@/api/suppliers";
import { listProducts } from "@/api/products";
import { listWarehouses } from "@/api/inventory";
import {
  cancelPurchaseOrder,
  confirmPurchaseOrder,
  createPurchaseOrder,
  createPurchasePayment,
  getPurchaseOrder,
  listPurchaseOrders,
  receivePurchaseOrder,
  updatePurchaseOrder,
} from "@/api/purchase";
import { t } from "@/i18n";
import type { SupplierRecord } from "@/types/supplier";
import type { ProductRecord } from "@/types/product";
import type { Warehouse } from "@/types/inventory";
import type { PurchaseOrderDetail, PurchaseOrderListItem } from "@/types/purchase";

interface PurchaseFormItem {
  product_id?: number;
  product_code: string;
  product_name: string;
  product_barcode: string;
  product_spec: string;
  product_model: string;
  unit_name: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  remark: string;
}

const loading = ref(false);
const router = useRouter();
const suppliersLoading = ref(false);
const productsLoading = ref(false);
const tableData = ref<PurchaseOrderListItem[]>([]);
const suppliers = ref<SupplierRecord[]>([]);
const products = ref<ProductRecord[]>([]);
const warehouses = ref<Warehouse[]>([]);
const total = ref(0);
const formDialogVisible = ref(false);
const detailDialogVisible = ref(false);
const receiveDialogVisible = ref(false);
const paymentDialogVisible = ref(false);
const editingId = ref<number | null>(null);
const currentDetail = ref<PurchaseOrderDetail | null>(null);
const formRef = ref<FormInstance>();
const paymentFormRef = ref<FormInstance>();

const query = reactive({
  keyword: "",
  supplierId: undefined as number | undefined,
  status: "",
  receiveStatus: "",
  paymentStatus: "",
  dateRange: [] as string[],
  page: 1,
  pageSize: 10,
});

const form = reactive({
  supplier_id: undefined as number | undefined,
  warehouse_id: undefined as number | undefined,
  order_date: "",
  discount_amount: 0,
  remark: "",
  items: [] as PurchaseFormItem[],
});

const receiveForm = reactive({
  remark: "",
  items: [] as Array<{ item_id: number; product_name: string; unreceived_quantity: number; quantity: number }>,
});

const paymentForm = reactive({
  payment_date: "",
  amount: 0,
  method: "cash" as "cash" | "wechat" | "alipay" | "bank" | "other",
  remark: "",
});

const formRules: FormRules = {
  supplier_id: [{ required: true, message: t("purchaseSupplierRequired"), trigger: "change" }],
  order_date: [{ required: true, message: t("purchaseDateRequired"), trigger: "change" }],
};

const paymentRules: FormRules = {
  amount: [{ required: true, message: t("purchasePaymentAmountRequired"), trigger: "blur" }],
  payment_date: [{ required: true, message: t("purchasePaymentDateRequired"), trigger: "change" }],
};

const defaultWarehouseId = computed(() => warehouses.value.find((item) => item.is_default)?.id);
const formTotalAmount = computed(() => form.items.reduce((sum, item) => sum + lineAmount(item), 0));
const formPayableAmount = computed(() => Math.max(0, formTotalAmount.value - form.discount_amount));

function today() {
  return new Date().toISOString().slice(0, 10);
}

function money(value: number) {
  return value.toFixed(2);
}

function qty(value: number) {
  return value.toFixed(3);
}

function lineAmount(item: PurchaseFormItem) {
  return Math.max(0, item.quantity * item.unit_price - item.discount_amount);
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function statusText(value: string) {
  const map: Record<string, string> = {
    draft: t("purchaseStatusDraft"),
    confirmed: t("purchaseStatusConfirmed"),
    cancelled: t("purchaseStatusCancelled"),
    not_received: t("receiveNotReceived"),
    partial_received: t("receivePartialReceived"),
    received: t("receiveReceived"),
    unpaid: t("paymentUnpaid"),
    partial_paid: t("paymentPartialPaid"),
    paid: t("paymentPaid"),
  };
  return map[value] || value;
}

function paymentMethodText(value: string) {
  const map: Record<string, string> = {
    cash: t("payCash"),
    wechat: t("payWechat"),
    alipay: t("payAlipay"),
    bank: t("payBank"),
    other: t("payOther"),
  };
  return map[value] || value;
}

async function fetchBaseData() {
  suppliersLoading.value = true;
  productsLoading.value = true;
  try {
    const [supplierResponse, productResponse, warehouseResponse] = await Promise.all([
      listSuppliers({ page: 1, page_size: 100, is_active: true }),
      listProducts({ page: 1, page_size: 100, is_active: true }),
      listWarehouses(),
    ]);
    suppliers.value = supplierResponse.data.items;
    products.value = productResponse.data.items;
    warehouses.value = warehouseResponse.data;
  } finally {
    suppliersLoading.value = false;
    productsLoading.value = false;
  }
}

async function fetchOrders() {
  loading.value = true;
  try {
    const response = await listPurchaseOrders({
      keyword: query.keyword || undefined,
      supplier_id: query.supplierId,
      status: query.status || undefined,
      receive_status: query.receiveStatus || undefined,
      payment_status: query.paymentStatus || undefined,
      start_date: query.dateRange[0],
      end_date: query.dateRange[1],
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
  await fetchOrders();
}

async function handleReset() {
  query.keyword = "";
  query.supplierId = undefined;
  query.status = "";
  query.receiveStatus = "";
  query.paymentStatus = "";
  query.dateRange = [];
  query.page = 1;
  await fetchOrders();
}

function resetForm() {
  editingId.value = null;
  form.supplier_id = undefined;
  form.warehouse_id = defaultWarehouseId.value;
  form.order_date = today();
  form.discount_amount = 0;
  form.remark = "";
  form.items = [emptyItem()];
}

function emptyItem(): PurchaseFormItem {
  return {
    product_id: undefined,
    product_code: "",
    product_name: "",
    product_barcode: "",
    product_spec: "",
    product_model: "",
    unit_name: "",
    quantity: 1,
    unit_price: 0,
    discount_amount: 0,
    remark: "",
  };
}

function openCreateDialog() {
  resetForm();
  formDialogVisible.value = true;
}

async function openEditDialog(row: PurchaseOrderListItem) {
  const response = await getPurchaseOrder(row.id);
  const order = response.data;
  editingId.value = order.id;
  form.supplier_id = order.supplier_id;
  form.warehouse_id = order.warehouse_id;
  form.order_date = order.order_date;
  form.discount_amount = Number(order.discount_amount);
  form.remark = order.remark || "";
  form.items = order.items.map((item) => ({
    product_id: item.product_id,
    product_code: item.product_code || "",
    product_name: item.product_name,
    product_barcode: item.product_barcode || "",
    product_spec: item.product_spec || "",
    product_model: item.product_model || "",
    unit_name: item.unit_name || "",
    quantity: Number(item.quantity),
    unit_price: Number(item.unit_price),
    discount_amount: Number(item.discount_amount),
    remark: item.remark || "",
  }));
  formDialogVisible.value = true;
}

function addItem() {
  form.items.push(emptyItem());
}

function removeItem(index: number) {
  if (form.items.length === 1) {
    ElMessage.warning(t("purchaseItemRequired"));
    return;
  }
  form.items.splice(index, 1);
}

function handleProductChange(item: PurchaseFormItem) {
  const product = products.value.find((row) => row.id === item.product_id);
  if (!product) {
    return;
  }
  item.product_code = product.code || "";
  item.product_name = product.name;
  item.product_barcode = product.barcode || "";
  item.product_spec = product.spec || "";
  item.product_model = product.model || "";
  item.unit_name = product.unit_name || "";
  item.unit_price = Number(product.purchase_price);
}

function buildPayload() {
  return {
    supplier_id: form.supplier_id as number,
    warehouse_id: form.warehouse_id || null,
    order_date: form.order_date,
    discount_amount: money(form.discount_amount),
    remark: form.remark || null,
    items: form.items.map((item) => ({
      product_id: item.product_id as number,
      quantity: qty(item.quantity),
      unit_price: money(item.unit_price),
      discount_amount: money(item.discount_amount),
      remark: item.remark || null,
    })),
  };
}

async function saveOrder() {
  await formRef.value?.validate();
  if (!form.items.length || form.items.some((item) => !item.product_id)) {
    ElMessage.error(t("purchaseItemRequired"));
    return;
  }
  if (form.items.some((item) => item.quantity <= 0 || item.unit_price < 0 || item.discount_amount < 0)) {
    ElMessage.error(t("purchaseItemInvalid"));
    return;
  }
  if (editingId.value) {
    await updatePurchaseOrder(editingId.value, buildPayload());
  } else {
    await createPurchaseOrder(buildPayload());
  }
  ElMessage.success(t("saveSuccess"));
  formDialogVisible.value = false;
  await fetchOrders();
}

async function openDetail(row: PurchaseOrderListItem) {
  const response = await getPurchaseOrder(row.id);
  currentDetail.value = response.data;
  detailDialogVisible.value = true;
}

async function handleConfirm(row: PurchaseOrderListItem) {
  await ElMessageBox.confirm(t("purchaseConfirmPrompt"), t("confirm"), { type: "warning" });
  await confirmPurchaseOrder(row.id);
  ElMessage.success(t("saveSuccess"));
  await fetchOrders();
}

async function openReceiveDialog(row: PurchaseOrderListItem) {
  const response = await getPurchaseOrder(row.id);
  currentDetail.value = response.data;
  receiveForm.remark = "";
  receiveForm.items = response.data.items
    .map((item) => ({
      item_id: item.id,
      product_name: item.product_name,
      unreceived_quantity: Number(item.quantity) - Number(item.received_quantity),
      quantity: Number(item.quantity) - Number(item.received_quantity),
    }))
    .filter((item) => item.unreceived_quantity > 0);
  if (!receiveForm.items.length) {
    ElMessage.info(t("nothingToReceive"));
    return;
  }
  receiveDialogVisible.value = true;
}

async function submitReceive() {
  if (!currentDetail.value) {
    return;
  }
  if (receiveForm.items.some((item) => item.quantity <= 0 || item.quantity > item.unreceived_quantity)) {
    ElMessage.error(t("receiveQuantityInvalid"));
    return;
  }
  await receivePurchaseOrder(currentDetail.value.id, {
    items: receiveForm.items.map((item) => ({ item_id: item.item_id, quantity: qty(item.quantity) })),
    remark: receiveForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  receiveDialogVisible.value = false;
  await fetchOrders();
}

async function openPaymentDialog(row: PurchaseOrderListItem) {
  const response = await getPurchaseOrder(row.id);
  currentDetail.value = response.data;
  paymentForm.payment_date = today();
  paymentForm.amount = Number(response.data.unpaid_amount);
  paymentForm.method = "cash";
  paymentForm.remark = "";
  paymentDialogVisible.value = true;
}

async function submitPayment() {
  await paymentFormRef.value?.validate();
  if (!currentDetail.value) {
    return;
  }
  if (paymentForm.amount <= 0 || paymentForm.amount > Number(currentDetail.value.unpaid_amount)) {
    ElMessage.error(t("purchasePaymentAmountInvalid"));
    return;
  }
  await createPurchasePayment(currentDetail.value.id, {
    payment_date: paymentForm.payment_date,
    amount: money(paymentForm.amount),
    method: paymentForm.method,
    remark: paymentForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  paymentDialogVisible.value = false;
  await fetchOrders();
}

async function handleCancel(row: PurchaseOrderListItem) {
  const result = await ElMessageBox.prompt(t("purchaseCancelReasonPrompt"), t("cancelPurchaseOrder"), {
    inputType: "textarea",
    inputValidator: (value) => Boolean(value?.trim()) || t("purchaseCancelReasonRequired"),
    type: "warning",
  });
  await cancelPurchaseOrder(row.id, result.value.trim());
  ElMessage.success(t("saveSuccess"));
  await fetchOrders();
}

function handlePrint(row: PurchaseOrderListItem) {
  router.push({ name: "purchaseOrderPrint", params: { id: row.id } });
}

onMounted(async () => {
  await fetchBaseData();
  await fetchOrders();
});
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar purchase-toolbar">
      <el-input v-model="query.keyword" :placeholder="t('purchaseKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      <el-select v-model="query.supplierId" :placeholder="t('supplierName')" clearable filterable>
        <el-option v-for="item in suppliers" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="query.status" :placeholder="t('purchaseStatus')" clearable>
        <el-option :label="t('purchaseStatusDraft')" value="draft" />
        <el-option :label="t('purchaseStatusConfirmed')" value="confirmed" />
        <el-option :label="t('purchaseStatusCancelled')" value="cancelled" />
      </el-select>
      <el-select v-model="query.receiveStatus" :placeholder="t('receiveStatus')" clearable>
        <el-option :label="t('receiveNotReceived')" value="not_received" />
        <el-option :label="t('receivePartialReceived')" value="partial_received" />
        <el-option :label="t('receiveReceived')" value="received" />
      </el-select>
      <el-select v-model="query.paymentStatus" :placeholder="t('paymentStatus')" clearable>
        <el-option :label="t('paymentUnpaid')" value="unpaid" />
        <el-option :label="t('paymentPartialPaid')" value="partial_paid" />
        <el-option :label="t('paymentPaid')" value="paid" />
      </el-select>
      <el-date-picker v-model="query.dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('startDate')" :end-placeholder="t('endDate')" />
      <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
      <el-button type="success" @click="openCreateDialog">{{ t("addPurchaseOrder") }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border class="data-table" :empty-text="t('noData')">
      <el-table-column prop="order_no" :label="t('purchaseOrderNo')" min-width="150" />
      <el-table-column prop="order_date" :label="t('purchaseDate')" min-width="110" />
      <el-table-column prop="supplier_name" :label="t('supplierName')" min-width="150" />
      <el-table-column :label="t('purchaseStatus')" width="110">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column :label="t('receiveStatus')" width="120">
        <template #default="{ row }">{{ statusText(row.receive_status) }}</template>
      </el-table-column>
      <el-table-column :label="t('paymentStatus')" width="120">
        <template #default="{ row }">{{ statusText(row.payment_status) }}</template>
      </el-table-column>
      <el-table-column prop="total_quantity" :label="t('totalQuantity')" min-width="110" align="right" />
      <el-table-column prop="payable_amount" :label="t('payableAmount')" min-width="110" align="right" />
      <el-table-column prop="paid_amount" :label="t('paidAmount')" min-width="110" align="right" />
      <el-table-column prop="unpaid_amount" :label="t('unpaidAmount')" min-width="110" align="right" />
      <el-table-column :label="t('createdAt')" min-width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('actions')" fixed="right" width="320">
        <template #default="{ row }">
          <el-button v-if="row.status !== 'draft'" size="small" @click="openDetail(row)">{{ t("detail") }}</el-button>
          <el-button v-if="row.status === 'draft'" size="small" @click="openEditDialog(row)">{{ t("edit") }}</el-button>
          <el-button v-if="row.status === 'draft'" size="small" type="primary" @click="handleConfirm(row)">{{ t("confirmPurchaseOrder") }}</el-button>
          <el-button v-if="row.status === 'confirmed'" size="small" @click="openReceiveDialog(row)">{{ t("receivePurchaseOrder") }}</el-button>
          <el-button v-if="row.status === 'confirmed'" size="small" @click="openPaymentDialog(row)">{{ t("payPurchaseOrder") }}</el-button>
          <el-button size="small" @click="handlePrint(row)">{{ t("print") }}</el-button>
          <el-button v-if="row.status !== 'cancelled'" size="small" type="danger" @click="handleCancel(row)">{{ t("cancelPurchaseOrder") }}</el-button>
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
        @size-change="fetchOrders"
        @current-change="fetchOrders"
      />
    </div>

    <el-dialog v-model="formDialogVisible" :title="editingId ? t('editPurchaseOrder') : t('addPurchaseOrder')" width="1080px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <div class="purchase-form-grid">
          <el-form-item :label="t('supplierName')" prop="supplier_id">
            <el-select v-model="form.supplier_id" filterable :loading="suppliersLoading" class="form-wide-control">
              <el-option v-for="item in suppliers" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('warehouse')">
            <el-select v-model="form.warehouse_id" class="form-wide-control">
              <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('purchaseDate')" prop="order_date">
            <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" class="form-wide-control" />
          </el-form-item>
          <el-form-item :label="t('orderDiscount')">
            <el-input-number v-model="form.discount_amount" :min="0" :precision="2" class="form-wide-control" />
          </el-form-item>
        </div>
        <el-form-item :label="t('remark')">
          <el-input v-model="form.remark" />
        </el-form-item>

        <div class="purchase-items-header">
          <strong>{{ t("purchaseItems") }}</strong>
          <el-button size="small" type="primary" @click="addItem">{{ t("add") }}</el-button>
        </div>
        <el-table :data="form.items" border :empty-text="t('noData')">
          <el-table-column :label="t('productName')" min-width="180">
            <template #default="{ row }">
              <el-select v-model="row.product_id" filterable :loading="productsLoading" @change="handleProductChange(row)">
                <el-option v-for="item in products" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="product_code" :label="t('productCode')" min-width="110" />
          <el-table-column prop="product_spec" :label="t('productSpec')" min-width="110" />
          <el-table-column prop="unit_name" :label="t('productUnit')" width="90" />
          <el-table-column :label="t('quantity')" width="150">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="0.001" :precision="3" />
            </template>
          </el-table-column>
          <el-table-column :label="t('unitPrice')" width="150">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" />
            </template>
          </el-table-column>
          <el-table-column :label="t('lineDiscount')" width="150">
            <template #default="{ row }">
              <el-input-number v-model="row.discount_amount" :min="0" :precision="2" />
            </template>
          </el-table-column>
          <el-table-column :label="t('lineAmount')" width="110" align="right">
            <template #default="{ row }">{{ money(lineAmount(row)) }}</template>
          </el-table-column>
          <el-table-column :label="t('remark')" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.remark" />
            </template>
          </el-table-column>
          <el-table-column :label="t('actions')" width="90">
            <template #default="{ $index }">
              <el-button size="small" type="danger" @click="removeItem($index)">{{ t("delete") }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="purchase-total-bar">
          <span>{{ t("totalAmount") }}: {{ money(formTotalAmount) }}</span>
          <span>{{ t("payableAmount") }}: {{ money(formPayableAmount) }}</span>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="formDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="saveOrder">{{ t("saveDraft") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" :title="t('purchaseOrderDetail')" width="960px">
      <template v-if="currentDetail">
        <el-descriptions :column="3" border>
          <el-descriptions-item :label="t('purchaseOrderNo')">{{ currentDetail.order_no }}</el-descriptions-item>
          <el-descriptions-item :label="t('supplierName')">{{ currentDetail.supplier_name }}</el-descriptions-item>
          <el-descriptions-item :label="t('purchaseDate')">{{ currentDetail.order_date }}</el-descriptions-item>
          <el-descriptions-item :label="t('purchaseStatus')">{{ statusText(currentDetail.status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('receiveStatus')">{{ statusText(currentDetail.receive_status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('paymentStatus')">{{ statusText(currentDetail.payment_status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('payableAmount')">{{ currentDetail.payable_amount }}</el-descriptions-item>
          <el-descriptions-item :label="t('paidAmount')">{{ currentDetail.paid_amount }}</el-descriptions-item>
          <el-descriptions-item :label="t('unpaidAmount')">{{ currentDetail.unpaid_amount }}</el-descriptions-item>
        </el-descriptions>
        <h3>{{ t("purchaseItems") }}</h3>
        <el-table :data="currentDetail.items" border>
          <el-table-column prop="product_name" :label="t('productName')" />
          <el-table-column prop="quantity" :label="t('quantity')" align="right" />
          <el-table-column prop="received_quantity" :label="t('receivedQuantity')" align="right" />
          <el-table-column prop="unit_price" :label="t('unitPrice')" align="right" />
          <el-table-column prop="line_amount" :label="t('lineAmount')" align="right" />
        </el-table>
        <h3>{{ t("purchasePaymentRecords") }}</h3>
        <el-table :data="currentDetail.payments" border :empty-text="t('noData')">
          <el-table-column prop="payment_no" :label="t('purchasePaymentNo')" />
          <el-table-column prop="payment_date" :label="t('purchasePaymentDate')" />
          <el-table-column :label="t('purchasePaymentMethod')">
            <template #default="{ row }">{{ paymentMethodText(row.method) }}</template>
          </el-table-column>
          <el-table-column prop="amount" :label="t('amount')" align="right" />
          <el-table-column prop="remark" :label="t('remark')" />
        </el-table>
      </template>
    </el-dialog>

    <el-dialog v-model="receiveDialogVisible" :title="t('receivePurchaseOrder')" width="720px">
      <el-table :data="receiveForm.items" border>
        <el-table-column prop="product_name" :label="t('productName')" />
        <el-table-column prop="unreceived_quantity" :label="t('unreceivedQuantity')" align="right" />
        <el-table-column :label="t('receiveQuantity')" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.quantity" :min="0.001" :max="row.unreceived_quantity" :precision="3" />
          </template>
        </el-table-column>
      </el-table>
      <el-input v-model="receiveForm.remark" class="dialog-remark" type="textarea" :rows="3" :placeholder="t('remark')" />
      <template #footer>
        <el-button @click="receiveDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitReceive">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="paymentDialogVisible" :title="t('payPurchaseOrder')" width="520px">
      <el-form ref="paymentFormRef" :model="paymentForm" :rules="paymentRules" label-width="100px">
        <el-form-item :label="t('purchasePaymentDate')" prop="payment_date">
          <el-date-picker v-model="paymentForm.payment_date" type="date" value-format="YYYY-MM-DD" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('purchasePaymentAmount')" prop="amount">
          <el-input-number v-model="paymentForm.amount" :min="0.01" :max="Number(currentDetail?.unpaid_amount || 0)" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('purchasePaymentMethod')">
          <el-select v-model="paymentForm.method" class="form-wide-control">
            <el-option :label="t('payCash')" value="cash" />
            <el-option :label="t('payWechat')" value="wechat" />
            <el-option :label="t('payAlipay')" value="alipay" />
            <el-option :label="t('payBank')" value="bank" />
            <el-option :label="t('payOther')" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="paymentForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitPayment">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>
  </section>
</template>
