import { http } from "@/api/http";
import type {
  InitialStockPayload,
  InventoryAdjustmentPayload,
  InventoryListResponse,
  InventoryRecord,
  StockMovementListResponse,
  StockMovementRecord,
  Warehouse,
} from "@/types/inventory";

export interface InventoryListParams {
  keyword?: string;
  category_id?: number;
  warehouse_id?: number;
  low_stock_only?: boolean;
  page: number;
  page_size: number;
}

export interface StockMovementListParams {
  keyword?: string;
  product_id?: number;
  warehouse_id?: number;
  movement_type?: string;
  direction?: string;
  start_date?: string;
  end_date?: string;
  page: number;
  page_size: number;
}

export function listWarehouses() {
  return http.get<Warehouse[]>("/warehouses");
}

export function listInventory(params: InventoryListParams) {
  return http.get<InventoryListResponse>("/inventory", { params });
}

export function getInventory(productId: number, warehouseId?: number) {
  return http.get<InventoryRecord>(`/inventory/${productId}`, { params: { warehouse_id: warehouseId } });
}

export function setInitialStock(payload: InitialStockPayload) {
  return http.post<InventoryRecord>("/inventory/initial-stock", payload);
}

export function adjustInventory(payload: InventoryAdjustmentPayload) {
  return http.post<InventoryRecord>("/inventory/adjustments", payload);
}

export function listStockMovements(params: StockMovementListParams) {
  return http.get<StockMovementListResponse>("/stock-movements", { params });
}

export function getStockMovement(id: number) {
  return http.get<StockMovementRecord>(`/stock-movements/${id}`);
}
