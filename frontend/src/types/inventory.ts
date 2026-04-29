export interface Warehouse {
  id: number;
  name: string;
  sort_order: number;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryRecord {
  product_id: number;
  product_code: string | null;
  barcode: string | null;
  product_name: string;
  category_id: number | null;
  category_name: string | null;
  unit_id: number | null;
  unit_name: string | null;
  spec: string | null;
  model: string | null;
  brand: string | null;
  warehouse_id: number;
  warehouse_name: string;
  quantity_on_hand: string;
  average_cost: string;
  total_cost: string;
  stock_warning_qty: string;
  is_low_stock: boolean;
  updated_at: string | null;
}

export interface InventoryListResponse {
  items: InventoryRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface InitialStockPayload {
  product_id: number;
  warehouse_id?: number | null;
  quantity: string;
  unit_cost: string;
  remark?: string | null;
}

export interface InventoryAdjustmentPayload {
  product_id: number;
  warehouse_id?: number | null;
  mode: "increase" | "decrease" | "set";
  quantity?: string | null;
  target_qty?: string | null;
  unit_cost?: string | null;
  remark?: string | null;
}

export interface StockMovementRecord {
  id: number;
  movement_no: string;
  product_id: number;
  product_code: string | null;
  barcode: string | null;
  product_name: string;
  warehouse_id: number;
  warehouse_name: string;
  movement_type: string;
  direction: string;
  quantity: string;
  unit_cost: string;
  amount: string;
  before_qty: string;
  after_qty: string;
  before_avg_cost: string;
  after_avg_cost: string;
  source_type: string;
  source_id: number | null;
  remark: string | null;
  created_by_id: number | null;
  created_by_name: string | null;
  created_at: string;
}

export interface StockMovementListResponse {
  items: StockMovementRecord[];
  total: number;
  page: number;
  page_size: number;
}
