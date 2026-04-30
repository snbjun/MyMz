<script setup lang="ts">
import { reactive, watch } from "vue";
import type { FormRules } from "element-plus";

import { t } from "@/i18n";
import type { PrintSetting, PrintSettingPayload } from "@/types/printing";

const props = defineProps<{
  modelValue: boolean;
  setting: PrintSetting | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  save: [payload: PrintSettingPayload];
}>();

const form = reactive({
  template_name: "",
  paper_size: "A4" as const,
  show_company_name: true,
  company_name: "",
  show_contact: false,
  contact_text: "",
  show_amount: true,
  show_unit_price: true,
  show_discount: true,
  show_remark: true,
  show_signature: true,
  footer_text: "",
});

const rules: FormRules = {
  template_name: [{ required: true, message: t("printTemplateNameRequired"), trigger: "blur" }],
};

watch(
  () => props.setting,
  (setting) => {
    if (!setting) return;
    form.template_name = setting.template_name;
    form.paper_size = setting.paper_size;
    form.show_company_name = setting.show_company_name;
    form.company_name = setting.company_name ?? "";
    form.show_contact = setting.show_contact;
    form.contact_text = setting.contact_text ?? "";
    form.show_amount = setting.show_amount;
    form.show_unit_price = setting.show_unit_price;
    form.show_discount = setting.show_discount;
    form.show_remark = setting.show_remark;
    form.show_signature = setting.show_signature;
    form.footer_text = setting.footer_text ?? "";
  },
  { immediate: true },
);

function closeDialog() {
  emit("update:modelValue", false);
}

function submit() {
  emit("save", { ...form });
}
</script>

<template>
  <el-dialog :model-value="modelValue" :title="t('printSettings')" width="620px" @update:model-value="emit('update:modelValue', $event)">
    <el-form :model="form" :rules="rules" label-width="150px">
      <el-form-item :label="t('printTemplateName')" prop="template_name">
        <el-input v-model="form.template_name" />
      </el-form-item>
      <el-form-item :label="t('printPaperSize')">
        <el-select v-model="form.paper_size">
          <el-option label="A4" value="A4" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('showCompanyName')">
        <el-switch v-model="form.show_company_name" />
      </el-form-item>
      <el-form-item v-if="form.show_company_name" :label="t('companyName')">
        <el-input v-model="form.company_name" />
      </el-form-item>
      <el-form-item :label="t('showContact')">
        <el-switch v-model="form.show_contact" />
      </el-form-item>
      <el-form-item v-if="form.show_contact" :label="t('contactText')">
        <el-input v-model="form.contact_text" />
      </el-form-item>
      <el-form-item :label="t('showAmount')">
        <el-switch v-model="form.show_amount" />
      </el-form-item>
      <el-form-item :label="t('showUnitPrice')">
        <el-switch v-model="form.show_unit_price" />
      </el-form-item>
      <el-form-item :label="t('showDiscount')">
        <el-switch v-model="form.show_discount" />
      </el-form-item>
      <el-form-item :label="t('showRemark')">
        <el-switch v-model="form.show_remark" />
      </el-form-item>
      <el-form-item :label="t('showSignature')">
        <el-switch v-model="form.show_signature" />
      </el-form-item>
      <el-form-item :label="t('footerText')">
        <el-input v-model="form.footer_text" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="closeDialog">{{ t("cancel") }}</el-button>
      <el-button type="primary" @click="submit">{{ t("save") }}</el-button>
    </template>
  </el-dialog>
</template>
