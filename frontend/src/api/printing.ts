import { http } from "@/api/http";
import type {
  PrintDocType,
  PrintSetting,
  PrintSettingPayload,
  PurchaseOrderPrintData,
  SalesOrderPrintData,
} from "@/types/printing";

export function listPrintSettings() {
  return http.get<PrintSetting[]>("/print-settings");
}

export function getPrintSetting(docType: PrintDocType) {
  return http.get<PrintSetting>(`/print-settings/${docType}`);
}

export function updatePrintSetting(docType: PrintDocType, payload: PrintSettingPayload) {
  return http.put<PrintSetting>(`/print-settings/${docType}`, payload);
}

export function getSalesOrderPrintData(id: number) {
  return http.get<SalesOrderPrintData>(`/print/sales-orders/${id}`);
}

export function getPurchaseOrderPrintData(id: number) {
  return http.get<PurchaseOrderPrintData>(`/print/purchase-orders/${id}`);
}

