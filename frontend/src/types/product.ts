export interface ProductCategory {
  id: number;
  name: string;
  sort_order: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductUnit {
  id: number;
  name: string;
  sort_order: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductRecord {
  id: number;
  code: string | null;
  barcode: string | null;
  name: string;
  category_id: number | null;
  category_name: string | null;
  unit_id: number | null;
  unit_name: string | null;
  spec: string | null;
  model: string | null;
  brand: string | null;
  origin: string | null;
  sale_price: string;
  purchase_price: string;
  wholesale_price: string;
  stock_warning_qty: string;
  image_url: string | null;
  remark: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: ProductRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProductPayload {
  code?: string | null;
  barcode?: string | null;
  name: string;
  category_id?: number | null;
  unit_id?: number | null;
  spec?: string | null;
  model?: string | null;
  brand?: string | null;
  origin?: string | null;
  sale_price: string;
  purchase_price: string;
  wholesale_price: string;
  stock_warning_qty: string;
  image_url?: string | null;
  remark?: string | null;
  is_active: boolean;
}
