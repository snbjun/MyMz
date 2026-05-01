<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import {
  createProduct,
  createProductCategory,
  createProductUnit,
  deleteProduct,
  deleteProductCategory,
  deleteProductUnit,
  listProductCategories,
  listProducts,
  listProductUnits,
  toggleProductActive,
  updateProduct,
  updateProductCategory,
  updateProductUnit,
} from "@/api/products";
import { t } from "@/i18n";
import { useAuthStore } from "@/stores/auth";
import type { ProductCategory, ProductPayload, ProductRecord, ProductUnit } from "@/types/product";
import { hasPermission, Permission } from "@/utils/permissions";

const authStore = useAuthStore();
const loading = ref(false);
const categoriesLoading = ref(false);
const unitsLoading = ref(false);
const tableData = ref<ProductRecord[]>([]);
const categories = ref<ProductCategory[]>([]);
const units = ref<ProductUnit[]>([]);
const total = ref(0);
const productDialogVisible = ref(false);
const categoryDialogVisible = ref(false);
const unitDialogVisible = ref(false);
const productEditing = ref(false);
const categoryEditingId = ref<number | null>(null);
const unitEditingId = ref<number | null>(null);
const productFormRef = ref<FormInstance>();
const categoryFormRef = ref<FormInstance>();
const unitFormRef = ref<FormInstance>();
const canManageProducts = computed(() => hasPermission(authStore.user, Permission.PRODUCTS_MANAGE));

const query = reactive({
  keyword: "",
  categoryId: undefined as number | undefined,
  unitId: undefined as number | undefined,
  activeStatus: "" as "" | "true" | "false",
  page: 1,
  pageSize: 10,
});

const productForm = reactive({
  id: 0,
  code: "",
  barcode: "",
  name: "",
  category_id: undefined as number | undefined,
  unit_id: undefined as number | undefined,
  spec: "",
  model: "",
  brand: "",
  origin: "",
  sale_price: 0,
  purchase_price: 0,
  wholesale_price: 0,
  stock_warning_qty: 0,
  image_url: "",
  is_active: true,
  remark: "",
});

const categoryForm = reactive({
  name: "",
  sort_order: 0,
  is_default: false,
});

const unitForm = reactive({
  name: "",
  sort_order: 0,
  is_default: false,
});

const productRules: FormRules = {
  name: [{ required: true, message: t("productNameRequired"), trigger: "blur" }],
};

const categoryRules: FormRules = {
  name: [{ required: true, message: t("categoryNameRequired"), trigger: "blur" }],
};

const unitRules: FormRules = {
  name: [{ required: true, message: t("unitNameRequired"), trigger: "blur" }],
};

const defaultCategoryId = computed(() => categories.value.find((item) => item.is_default)?.id);
const defaultUnitId = computed(() => units.value.find((item) => item.is_default)?.id);

function money(value: number) {
  return value.toFixed(2);
}

function quantity(value: number) {
  return value.toFixed(3);
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function resetProductForm() {
  productForm.id = 0;
  productForm.code = "";
  productForm.barcode = "";
  productForm.name = "";
  productForm.category_id = defaultCategoryId.value;
  productForm.unit_id = defaultUnitId.value;
  productForm.spec = "";
  productForm.model = "";
  productForm.brand = "";
  productForm.origin = "";
  productForm.sale_price = 0;
  productForm.purchase_price = 0;
  productForm.wholesale_price = 0;
  productForm.stock_warning_qty = 0;
  productForm.image_url = "";
  productForm.is_active = true;
  productForm.remark = "";
}

function buildProductPayload(): ProductPayload {
  return {
    code: productForm.code || null,
    barcode: productForm.barcode || null,
    name: productForm.name,
    category_id: productForm.category_id || null,
    unit_id: productForm.unit_id || null,
    spec: productForm.spec || null,
    model: productForm.model || null,
    brand: productForm.brand || null,
    origin: productForm.origin || null,
    sale_price: money(productForm.sale_price),
    purchase_price: money(productForm.purchase_price),
    wholesale_price: money(productForm.wholesale_price),
    stock_warning_qty: quantity(productForm.stock_warning_qty),
    image_url: productForm.image_url || null,
    remark: productForm.remark || null,
    is_active: productForm.is_active,
  };
}

async function fetchCategories() {
  categoriesLoading.value = true;
  try {
    const response = await listProductCategories();
    categories.value = response.data;
  } finally {
    categoriesLoading.value = false;
  }
}

async function fetchUnits() {
  unitsLoading.value = true;
  try {
    const response = await listProductUnits();
    units.value = response.data;
  } finally {
    unitsLoading.value = false;
  }
}

async function fetchProducts() {
  loading.value = true;
  try {
    const response = await listProducts({
      keyword: query.keyword || undefined,
      category_id: query.categoryId,
      unit_id: query.unitId,
      is_active: query.activeStatus === "" ? undefined : query.activeStatus === "true",
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
  await fetchProducts();
}

async function handleReset() {
  query.keyword = "";
  query.categoryId = undefined;
  query.unitId = undefined;
  query.activeStatus = "";
  query.page = 1;
  await fetchProducts();
}

function openCreateProductDialog() {
  productEditing.value = false;
  resetProductForm();
  productDialogVisible.value = true;
}

function openEditProductDialog(row: ProductRecord) {
  productEditing.value = true;
  productForm.id = row.id;
  productForm.code = row.code || "";
  productForm.barcode = row.barcode || "";
  productForm.name = row.name;
  productForm.category_id = row.category_id || undefined;
  productForm.unit_id = row.unit_id || undefined;
  productForm.spec = row.spec || "";
  productForm.model = row.model || "";
  productForm.brand = row.brand || "";
  productForm.origin = row.origin || "";
  productForm.sale_price = Number(row.sale_price);
  productForm.purchase_price = Number(row.purchase_price);
  productForm.wholesale_price = Number(row.wholesale_price);
  productForm.stock_warning_qty = Number(row.stock_warning_qty);
  productForm.image_url = row.image_url || "";
  productForm.is_active = row.is_active;
  productForm.remark = row.remark || "";
  productDialogVisible.value = true;
}

async function saveProduct() {
  await productFormRef.value?.validate();
  if (productEditing.value) {
    await updateProduct(productForm.id, buildProductPayload());
  } else {
    await createProduct(buildProductPayload());
  }
  ElMessage.success(t("saveSuccess"));
  productDialogVisible.value = false;
  await fetchProducts();
}

async function handleToggle(row: ProductRecord) {
  await toggleProductActive(row.id);
  ElMessage.success(t("toggleSuccess"));
  await fetchProducts();
}

async function handleDelete(row: ProductRecord) {
  await ElMessageBox.confirm(t("productDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteProduct(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchProducts();
}

function openCategoryDialog() {
  categoryEditingId.value = null;
  categoryForm.name = "";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  categoryDialogVisible.value = true;
}

function editCategory(row: ProductCategory) {
  categoryEditingId.value = row.id;
  categoryForm.name = row.name;
  categoryForm.sort_order = row.sort_order;
  categoryForm.is_default = row.is_default;
}

async function saveCategory() {
  await categoryFormRef.value?.validate();
  const payload = {
    name: categoryForm.name,
    sort_order: categoryForm.sort_order,
    is_default: categoryForm.is_default,
  };
  if (categoryEditingId.value) {
    await updateProductCategory(categoryEditingId.value, payload);
  } else {
    await createProductCategory(payload);
  }
  ElMessage.success(t("saveSuccess"));
  categoryEditingId.value = null;
  categoryForm.name = "";
  categoryForm.sort_order = 0;
  categoryForm.is_default = false;
  await fetchCategories();
}

async function removeCategory(row: ProductCategory) {
  await ElMessageBox.confirm(t("categoryDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteProductCategory(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchCategories();
  await fetchProducts();
}

function openUnitDialog() {
  unitEditingId.value = null;
  unitForm.name = "";
  unitForm.sort_order = 0;
  unitForm.is_default = false;
  unitDialogVisible.value = true;
}

function editUnit(row: ProductUnit) {
  unitEditingId.value = row.id;
  unitForm.name = row.name;
  unitForm.sort_order = row.sort_order;
  unitForm.is_default = row.is_default;
}

async function saveUnit() {
  await unitFormRef.value?.validate();
  const payload = {
    name: unitForm.name,
    sort_order: unitForm.sort_order,
    is_default: unitForm.is_default,
  };
  if (unitEditingId.value) {
    await updateProductUnit(unitEditingId.value, payload);
  } else {
    await createProductUnit(payload);
  }
  ElMessage.success(t("saveSuccess"));
  unitEditingId.value = null;
  unitForm.name = "";
  unitForm.sort_order = 0;
  unitForm.is_default = false;
  await fetchUnits();
}

async function removeUnit(row: ProductUnit) {
  await ElMessageBox.confirm(t("unitDeleteConfirm"), t("delete"), { type: "warning" });
  await deleteProductUnit(row.id);
  ElMessage.success(t("deleteSuccess"));
  await fetchUnits();
  await fetchProducts();
}

onMounted(async () => {
  await Promise.all([fetchCategories(), fetchUnits()]);
  await fetchProducts();
});
</script>

<template>
  <section class="management-page">
    <div class="table-toolbar product-toolbar">
      <el-input v-model="query.keyword" :placeholder="t('productKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      <el-select v-model="query.categoryId" :placeholder="t('productCategory')" clearable>
        <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="query.unitId" :placeholder="t('productUnit')" clearable>
        <el-option v-for="item in units" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="query.activeStatus" :placeholder="t('isActive')" clearable>
        <el-option :label="t('enabled')" value="true" />
        <el-option :label="t('disabled')" value="false" />
      </el-select>
      <el-button type="primary" @click="handleSearch">{{ t("search") }}</el-button>
      <el-button @click="handleReset">{{ t("reset") }}</el-button>
      <el-button v-if="canManageProducts" type="success" @click="openCreateProductDialog">{{ t("addProduct") }}</el-button>
      <el-button v-if="canManageProducts" @click="openCategoryDialog">{{ t("categoryManage") }}</el-button>
      <el-button v-if="canManageProducts" @click="openUnitDialog">{{ t("unitManage") }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border class="data-table" :empty-text="t('noData')">
      <el-table-column prop="code" :label="t('productCode')" min-width="120" />
      <el-table-column prop="barcode" :label="t('productBarcode')" min-width="130" />
      <el-table-column prop="name" :label="t('productName')" min-width="150" />
      <el-table-column prop="category_name" :label="t('productCategory')" min-width="120" />
      <el-table-column prop="unit_name" :label="t('productUnit')" min-width="100" />
      <el-table-column prop="spec" :label="t('productSpec')" min-width="110" />
      <el-table-column prop="model" :label="t('productModel')" min-width="110" />
      <el-table-column prop="brand" :label="t('productBrand')" min-width="110" />
      <el-table-column prop="sale_price" :label="t('salePrice')" min-width="110" align="right" />
      <el-table-column prop="purchase_price" :label="t('purchasePrice')" min-width="110" align="right" />
      <el-table-column prop="stock_warning_qty" :label="t('stockWarningQty')" min-width="120" align="right" />
      <el-table-column prop="is_active" :label="t('status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? t("enabled") : t("disabled") }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('createdAt')" min-width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="t('actions')" fixed="right" width="220">
        <template #default="{ row }">
          <el-button v-if="canManageProducts" size="small" @click="openEditProductDialog(row)">{{ t("edit") }}</el-button>
          <el-button v-if="canManageProducts" size="small" @click="handleToggle(row)">{{ row.is_active ? t("disable") : t("enable") }}</el-button>
          <el-button v-if="canManageProducts" size="small" type="danger" @click="handleDelete(row)">{{ t("delete") }}</el-button>
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
        @size-change="fetchProducts"
        @current-change="fetchProducts"
      />
    </div>

    <el-drawer v-model="productDialogVisible" :title="productEditing ? t('editProduct') : t('addProduct')" size="620px">
      <el-form ref="productFormRef" :model="productForm" :rules="productRules" label-width="120px">
        <el-form-item :label="t('productName')" prop="name">
          <el-input v-model="productForm.name" />
        </el-form-item>
        <el-form-item :label="t('productCode')">
          <el-input v-model="productForm.code" />
        </el-form-item>
        <el-form-item :label="t('productBarcode')">
          <el-input v-model="productForm.barcode" />
        </el-form-item>
        <el-form-item :label="t('productCategory')">
          <el-select v-model="productForm.category_id" clearable class="form-wide-control">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('productUnit')">
          <el-select v-model="productForm.unit_id" clearable class="form-wide-control">
            <el-option v-for="item in units" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('productSpec')">
          <el-input v-model="productForm.spec" />
        </el-form-item>
        <el-form-item :label="t('productModel')">
          <el-input v-model="productForm.model" />
        </el-form-item>
        <el-form-item :label="t('productBrand')">
          <el-input v-model="productForm.brand" />
        </el-form-item>
        <el-form-item :label="t('productOrigin')">
          <el-input v-model="productForm.origin" />
        </el-form-item>
        <el-form-item :label="t('salePrice')">
          <el-input-number v-model="productForm.sale_price" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('purchasePrice')">
          <el-input-number v-model="productForm.purchase_price" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('wholesalePrice')">
          <el-input-number v-model="productForm.wholesale_price" :min="0" :precision="2" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('stockWarningQty')">
          <el-input-number v-model="productForm.stock_warning_qty" :min="0" :precision="3" class="form-wide-control" />
        </el-form-item>
        <el-form-item :label="t('imageUrl')">
          <el-input v-model="productForm.image_url" />
        </el-form-item>
        <el-form-item :label="t('isActive')">
          <el-switch v-model="productForm.is_active" />
        </el-form-item>
        <el-form-item :label="t('remark')">
          <el-input v-model="productForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="productDialogVisible = false">{{ t("cancel") }}</el-button>
        <el-button type="primary" @click="saveProduct">{{ t("confirm") }}</el-button>
      </template>
    </el-drawer>

    <el-dialog v-model="categoryDialogVisible" :title="t('categoryManage')" width="620px">
      <el-form ref="categoryFormRef" :model="categoryForm" :rules="categoryRules" inline>
        <el-form-item :label="t('categoryName')" prop="name">
          <el-input v-model="categoryForm.name" />
        </el-form-item>
        <el-form-item :label="t('sortOrder')">
          <el-input-number v-model="categoryForm.sort_order" :precision="0" />
        </el-form-item>
        <el-form-item :label="t('defaultCategory')">
          <el-switch v-model="categoryForm.is_default" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveCategory">{{ categoryEditingId ? t("confirm") : t("add") }}</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="categoriesLoading" :data="categories" border :empty-text="t('noData')">
        <el-table-column prop="name" :label="t('categoryName')" />
        <el-table-column prop="sort_order" :label="t('sortOrder')" width="110" />
        <el-table-column :label="t('defaultCategory')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">{{ t("yes") }}</el-tag>
            <span v-else>{{ t("no") }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('actions')" width="170">
          <template #default="{ row }">
            <el-button size="small" @click="editCategory(row)">{{ t("edit") }}</el-button>
            <el-button size="small" type="danger" :disabled="row.is_default" @click="removeCategory(row)">{{ t("delete") }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="unitDialogVisible" :title="t('unitManage')" width="620px">
      <el-form ref="unitFormRef" :model="unitForm" :rules="unitRules" inline>
        <el-form-item :label="t('unitName')" prop="name">
          <el-input v-model="unitForm.name" />
        </el-form-item>
        <el-form-item :label="t('sortOrder')">
          <el-input-number v-model="unitForm.sort_order" :precision="0" />
        </el-form-item>
        <el-form-item :label="t('defaultUnit')">
          <el-switch v-model="unitForm.is_default" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveUnit">{{ unitEditingId ? t("confirm") : t("add") }}</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="unitsLoading" :data="units" border :empty-text="t('noData')">
        <el-table-column prop="name" :label="t('unitName')" />
        <el-table-column prop="sort_order" :label="t('sortOrder')" width="110" />
        <el-table-column :label="t('defaultUnit')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">{{ t("yes") }}</el-tag>
            <span v-else>{{ t("no") }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('actions')" width="170">
          <template #default="{ row }">
            <el-button size="small" @click="editUnit(row)">{{ t("edit") }}</el-button>
            <el-button size="small" type="danger" :disabled="row.is_default" @click="removeUnit(row)">{{ t("delete") }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </section>
</template>
