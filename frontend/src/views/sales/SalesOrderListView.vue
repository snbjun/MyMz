<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import { listCustomers } from "@/api/customers";
import { listProducts } from "@/api/products";
import { listWarehouses } from "@/api/inventory";
import {
  cancelSalesOrder,
  confirmSalesOrder,
  createSalesOrder,
  createSalesPayment,
  getSalesOrder,
  listSalesOrders,
  shipSalesOrder,
  updateSalesOrder,
} from "@/api/sales";
import { t } from "@/i18n";
import type { CustomerRecord } from "@/types/customer";
import type { ProductRecord } from "@/types/product";
import type { Warehouse } from "@/types/inventory";
import type { SalesOrderDetail, SalesOrderListItem } from "@/types/sales";

interface SalesFormItem {
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
const customersLoading = ref(false);
const productsLoading = ref(false);
const tableData = ref<SalesOrderListItem[]>([]);
const customers = ref<CustomerRecord[]>([]);
const products = ref<ProductRecord[]>([]);
const warehouses = ref<Warehouse[]>([]);
const total = ref(0);
const formDialogVisible = ref(false);
const detailDialogVisible = ref(false);
const shipDialogVisible = ref(false);
const paymentDialogVisible = ref(false);
const editingId = ref<number | null>(null);
const currentDetail = ref<SalesOrderDetail | null>(null);
const formRef = ref<FormInstance>();
const paymentFormRef = ref<FormInstance>();

const query = reactive({
  keyword: "",
  customerId: undefined as number | undefined,
  status: "",
  deliveryStatus: "",
  paymentStatus: "",
  dateRange: [] as string[],
  page: 1,
  pageSize: 10,
});

const form = reactive({
  customer_id: undefined as number | undefined,
  warehouse_id: undefined as number | undefined,
  order_date: "",
  discount_amount: 0,
  remark: "",
  items: [] as SalesFormItem[],
});

const shipForm = reactive({
  remark: "",
  items: [] as Array<{ item_id: number; product_name: string; unshipped_quantity: number; quantity: number }>,
});

const paymentForm = reactive({
  payment_date: "",
  amount: 0,
  method: "cash" as "cash" | "wechat" | "alipay" | "bank" | "other",
  remark: "",
});

const formRules: FormRules = {
  customer_id: [{ required: true, message: t("salesCustomerRequired"), trigger: "change" }],
  order_date: [{ required: true, message: t("salesDateRequired"), trigger: "change" }],
};

const paymentRules: FormRules = {
  amount: [{ required: true, message: t("paymentAmountRequired"), trigger: "blur" }],
  payment_date: [{ required: true, message: t("paymentDateRequired"), trigger: "change" }],
};

const defaultWarehouseId = computed(() => warehouses.value.find((item) => item.is_default)?.id);
const formTotalAmount = computed(() => form.items.reduce((sum, item) => sum + lineAmount(item), 0));
const formReceivableAmount = computed(() => Math.max(0, formTotalAmount.value - form.discount_amount));

function today() {
  return new Date().toISOString().slice(0, 10);
}

function money(value: number) {
  return value.toFixed(2);
}

function qty(value: number) {
  return value.toFixed(3);
}

function lineAmount(item: SalesFormItem) {
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
    draft: t("salesStatusDraft"),
    confirmed: t("salesStatusConfirmed"),
    cancelled: t("salesStatusCancelled"),
    not_shipped: t("deliveryNotShipped"),
    partial_shipped: t("deliveryPartialShipped"),
    shipped: t("deliveryShipped"),
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
  customersLoading.value = true;
  productsLoading.value = true;
  try {
    const [customerResponse, productResponse, warehouseResponse] = await Promise.all([
      listCustomers({ page: 1, page_size: 100, is_active: true }),
      listProducts({ page: 1, page_size: 100, is_active: true }),
      listWarehouses(),
    ]);
    customers.value = customerResponse.data.items;
    products.value = productResponse.data.items;
    warehouses.value = warehouseResponse.data;
  } finally {
    customersLoading.value = false;
    productsLoading.value = false;
  }
}

async function fetchOrders() {
  loading.value = true;
  try {
    const response = await listSalesOrders({
      keyword: query.keyword || undefined,
      customer_id: query.customerId,
      status: query.status || undefined,
      delivery_status: query.deliveryStatus || undefined,
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
  query.customerId = undefined;
  query.status = "";
  query.deliveryStatus = "";
  query.paymentStatus = "";
  query.dateRange = [];
  query.page = 1;
  await fetchOrders();
}

function resetForm() {
  editingId.value = null;
  form.customer_id = undefined;
  form.warehouse_id = defaultWarehouseId.value;
  form.order_date = today();
  form.discount_amount = 0;
  form.remark = "";
  form.items = [emptyItem()];
}

function emptyItem(): SalesFormItem {
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

async function openEditDialog(row: SalesOrderListItem) {
  const response = await getSalesOrder(row.id);
  const order = response.data;
  editingId.value = order.id;
  form.customer_id = order.customer_id;
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
    ElMessage.warning(t("salesItemRequired"));
    return;
  }
  form.items.splice(index, 1);
}

function handleProductChange(item: SalesFormItem) {
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
  item.unit_price = Number(product.sale_price);
}

function buildPayload() {
  return {
    customer_id: form.customer_id as number,
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
    ElMessage.error(t("salesItemRequired"));
    return;
  }
  if (form.items.some((item) => item.quantity <= 0 || item.unit_price < 0 || item.discount_amount < 0)) {
    ElMessage.error(t("salesItemInvalid"));
    return;
  }
  if (editingId.value) {
    await updateSalesOrder(editingId.value, buildPayload());
  } else {
    await createSalesOrder(buildPayload());
  }
  ElMessage.success(t("saveSuccess"));
  formDialogVisible.value = false;
  await fetchOrders();
}

async function openDetail(row: SalesOrderListItem) {
  const response = await getSalesOrder(row.id);
  currentDetail.value = response.data;
  detailDialogVisible.value = true;
}

async function handleConfirm(row: SalesOrderListItem) {
  await ElMessageBox.confirm(t("salesConfirmPrompt"), t("confirm"), { type: "warning" });
  await confirmSalesOrder(row.id);
  ElMessage.success(t("saveSuccess"));
  await fetchOrders();
}

async function openShipDialog(row: SalesOrderListItem) {
  const response = await getSalesOrder(row.id);
  currentDetail.value = response.data;
  shipForm.remark = "";
  shipForm.items = response.data.items
    .map((item) => ({
      item_id: item.id,
      product_name: item.product_name,
      unshipped_quantity: Number(item.quantity) - Number(item.shipped_quantity),
      quantity: Number(item.quantity) - Number(item.shipped_quantity),
    }))
    .filter((item) => item.unshipped_quantity > 0);
  if (!shipForm.items.length) {
    ElMessage.info(t("nothingToShip"));
    return;
  }
  shipDialogVisible.value = true;
}

async function submitShip() {
  if (!currentDetail.value) {
    return;
  }
  if (shipForm.items.some((item) => item.quantity <= 0 || item.quantity > item.unshipped_quantity)) {
    ElMessage.error(t("shipQuantityInvalid"));
    return;
  }
  await shipSalesOrder(currentDetail.value.id, {
    items: shipForm.items.map((item) => ({ item_id: item.item_id, quantity: qty(item.quantity) })),
    remark: shipForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  shipDialogVisible.value = false;
  await fetchOrders();
}

async function openPaymentDialog(row: SalesOrderListItem) {
  const response = await getSalesOrder(row.id);
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
    ElMessage.error(t("paymentAmountInvalid"));
    return;
  }
  await createSalesPayment(currentDetail.value.id, {
    payment_date: paymentForm.payment_date,
    amount: money(paymentForm.amount),
    method: paymentForm.method,
    remark: paymentForm.remark || null,
  });
  ElMessage.success(t("saveSuccess"));
  paymentDialogVisible.value = false;
  await fetchOrders();
}

async function handleCancel(row: SalesOrderListItem) {
  const result = await ElMessageBox.prompt(t("salesCancelReasonPrompt"), t("cancelSalesOrder"), {
    inputType: "textarea",
    inputValidator: (value) => Boolean(value?.trim()) || t("salesCancelReasonRequired"),
    type: "warning",
  });
  await cancelSalesOrder(row.id, result.value.trim());
  ElMessage.success(t("saveSuccess"));
  await fetchOrders();
}

function handlePrint() {
  ElMessage.info(t("printComingSoon"));
}

onMounted(async () => {
  await fetchBaseData();
  await fetchOrders();
});
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar sales-toolbar">
      <el-input v-model="query.keyword" :placeholder="t('salesKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      <el-select v-model="query.customerId" :placeholder="t('customerName')" clearable filterable>
        <el-option v-for="item in customers" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="query.status" :placeholder="t('salesStatus')" clearable>
        <el-option :label="t('salesStatusDraft')" value="draft" />
        <el-option :label="t('salesStatusConfirmed')" value="confirmed" />
        <el-option :label="t('salesStatusCancelled')" value="cancelled" />
      </el-select>
      <el-select v-model="query.deliveryStatus" :placeholder="t('deliveryStatus')" clearable>
        <el-option :label="t('deliveryNotShipped')" value="not_shipped" />
        <el-option :label="t('deliveryPartialShipped')" value="partial_shipped" />
        <el-option :label="t('deliveryShipped')" value="shipped" />
      </el-select>
      <el-select v-model="query.paymentStatus" :placeholder="t('paymentStatus')" clearable>
        <el-option :label="t('paymentUnpaid')" value="unpaid" />
        <el-option :label="t('paymentPartialPaid')" value="partial_paid" />
        <el-option :label="t('paymentPaid')" value="paid" />
      </el-select>
      <el-date-picker v-model="query.dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('startDate')" :end-placeholder="t('endDate')" />
      <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
      <el-button type="success" @click="openCreateDialog">{{ t("addSalesOrder") }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border class="data-table" :empty-text="t('noData')">
      <el-table-column prop="order_no" :label="t('salesOrderNo')" min-width="150" />
      <el-table-column prop="order_date" :label="t('salesDate')" min-width="110" />
      <el-table-column prop="customer_name" :label="t('customerName')" min-width="150" />
      <el-table-column :label="t('salesStatus')" width="110">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column :label="t('deliveryStatus')" width="120">
        <template #default="{ row }">{{ statusText(row.delivery_status) }}</template>
      </el-table-column>
      <el-table-column :label="t('paymentStatus')" width="120">
        <template #default="{ row }">{{ statusText(row.payment_status) }}</template>
      </el-table-column>
      <el-table-column prop="total_quantity" :label="t('totalQuantity')" min-width="110" align="right" />
      <el-table-column prop="receivable_amount" :label="t('receivableAmount')" min-width="110" align="right" />
      <el-table-column prop="paid_amount" :label="t('paidAmount')" min-width="110" align="right" />
      <el-table-column prop="unpaid_amount" :label="t('unpaidAmount')" min-width="110" align="right" />
      <el-table-column :label="t('createdAt')" min-width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('actions')" fixed="right" width="320">
        <template #default="{ row }">
          <el-button v-if="row.status !== 'draft'" size="small" @click="openDetail(row)">{{ t("detail") }}</el-button>
          <el-button v-if="row.status === 'draft'" size="small" @click="openEditDialog(row)">{{ t("edit") }}</el-button>
          <el-button v-if="row.status === 'draft'" size="small" type="primary" @click="handleConfirm(row)">{{ t("confirmSalesOrder") }}</el-button>
          <el-button v-if="row.status === 'confirmed'" size="small" @click="openShipDialog(row)">{{ t("shipSalesOrder") }}</el-button>
          <el-button v-if="row.status === 'confirmed'" size="small" @click="openPaymentDialog(row)">{{ t("receivePayment") }}</el-button>
          <el-button v-if="row.status === 'confirmed'" size="small" @click="handlePrint">{{ t("print") }}</el-button>
          <el-button v-if="row.status !== 'cancelled'" size="small" type="danger" @click="handleCancel(row)">{{ t("cancelSalesOrder") }}</el-button>
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

    <el-dialog v-model="formDialogVisible" :title="editingId ? t('editSalesOrder') : t('addSalesOrder')" width="1080px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <div class="sales-form-grid">
          <el-form-item :label="t('customerName')" prop="customer_id">
            <el-select v-model="form.customer_id" filterable :loading="customersLoading" class="form-wide-control">
              <el-option v-for="item in customers" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('warehouse')">
            <el-select v-model="form.warehouse_id" class="form-wide-control">
              <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('salesDate')" prop="order_date">
            <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" class="form-wide-control" />
          </el-form-item>
          <el-form-item :label="t('orderDiscount')">
            <el-input-number v-model="form.discount_amount" :min="0" :precision="2" class="form-wide-control" />
          </el-form-item>
        </div>
        <el-form-item :label="t('remark')">
          <el-input v-model="form.remark" />
        </el-form-item>

        <div class="sales-items-header">
          <strong>{{ t("salesItems") }}</strong>
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
        <div class="sales-total-bar">
          <span>{{ t("totalAmount") }}: {{ money(formTotalAmount) }}</span>
          <span>{{ t("receivableAmount") }}: {{ money(formReceivableAmount) }}</span>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="formDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="saveOrder">{{ t("saveDraft") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" :title="t('salesOrderDetail')" width="960px">
      <template v-if="currentDetail">
        <el-descriptions :column="3" border>
          <el-descriptions-item :label="t('salesOrderNo')">{{ currentDetail.order_no }}</el-descriptions-item>
          <el-descriptions-item :label="t('customerName')">{{ currentDetail.customer_name }}</el-descriptions-item>
          <el-descriptions-item :label="t('salesDate')">{{ currentDetail.order_date }}</el-descriptions-item>
          <el-descriptions-item :label="t('salesStatus')">{{ statusText(currentDetail.status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('deliveryStatus')">{{ statusText(currentDetail.delivery_status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('paymentStatus')">{{ statusText(currentDetail.payment_status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('receivableAmount')">{{ currentDetail.receivable_amount }}</el-descriptions-item>
          <el-descriptions-item :label="t('paidAmount')">{{ currentDetail.paid_amount }}</el-descriptions-item>
          <el-descriptions-item :label="t('unpaidAmount')">{{ currentDetail.unpaid_amount }}</el-descriptions-item>
        </el-descriptions>
        <h3>{{ t("salesItems") }}</h3>
        <el-table :data="currentDetail.items" border>
          <el-table-column prop="product_name" :label="t('productName')" />
          <el-table-column prop="quantity" :label="t('quantity')" align="right" />
          <el-table-column prop="shipped_quantity" :label="t('shippedQuantity')" align="right" />
          <el-table-column prop="unit_price" :label="t('unitPrice')" align="right" />
          <el-table-column prop="line_amount" :label="t('lineAmount')" align="right" />
        </el-table>
        <h3>{{ t("paymentRecords") }}</h3>
        <el-table :data="currentDetail.payments" border :empty-text="t('noData')">
          <el-table-column prop="payment_no" :label="t('paymentNo')" />
          <el-table-column prop="payment_date" :label="t('paymentDate')" />
          <el-table-column :label="t('paymentMethod')">
            <template #default="{ row }">{{ paymentMethodText(row.method) }}</template>
          </el-table-column>
          <el-table-column prop="amount" :label="t('amount')" align="right" />
          <el-table-column prop="remark" :label="t('remark')" />
        </el-table>
      </template>
    </el-dialog>

    <el-dialog v-model="shipDialogVisible" :title="t('shipSalesOrder')" width="720px">
      <el-table :data="shipForm.items" border>
        <el-table-column prop="product_name" :label="t('productName')" />
        <el-table-column prop="unshipped_quantity" :label="t('unshippedQuantity')" align="right" />
        <el-table-column :label="t('shipQuantity')" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.quantity" :min="0.001" :max="row.unshipped_quantity" :precision="3" />
          </template>
        </el-table-column>
      </el-table>
      <el-input v-model="shipForm.remark" class="dialog-remark" type="textarea" :rows="3" :placeholder="t('remark')" />
      <template #footer>
        <el-button @click="shipDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="submitShip">{{ t("confirm") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="paymentDialogVisible" :title="t('receivePayment')" width="520px">
      <el-form ref="paymentFormRef" :model="paymentForm" :rules="paymentRules" label-width="100px">
        <el-form-item :label="t('paymentDate')" prop="payment_date">
          <el-date-picker v-model="paymentForm.payment_date" type="date" value-format="YYYY-MM-DD" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('paymentAmount')" prop="amount">
          <el-input-number v-model="paymentForm.amount" :min="0.01" :max="Number(currentDetail?.unpaid_amount || 0)" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('paymentMethod')">
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
