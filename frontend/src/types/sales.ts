export interface SalesOrderItemPayload {
  product_id: number;
  quantity: string;
  unit_price: string;
  discount_amount: string;
  remark?: string | null;
}

export interface SalesOrderPayload {
  customer_id: number;
  warehouse_id?: number | null;
  order_date: string;
  discount_amount: string;
  remark?: string | null;
  items: SalesOrderItemPayload[];
}

export interface SalesOrderItem {
  id: number;
  product_id: number;
  product_code: string | null;
  product_name: string;
  product_barcode: string | null;
  product_spec: string | null;
  product_model: string | null;
  unit_name: string | null;
  quantity: string;
  shipped_quantity: string;
  unit_price: string;
  discount_amount: string;
  line_amount: string;
  remark: string | null;
}

export interface SalesPayment {
  id: number;
  payment_no: string;
  payment_date: string;
  amount: string;
  method: string;
  remark: string | null;
  created_by_id: number | null;
  created_by_name: string | null;
  created_at: string;
}

export interface SalesOrderListItem {
  id: number;
  order_no: string;
  order_date: string;
  customer_id: number;
  customer_name: string;
  status: string;
  delivery_status: string;
  payment_status: string;
  total_quantity: string;
  receivable_amount: string;
  paid_amount: string;
  unpaid_amount: string;
  created_at: string;
}

export interface SalesOrderDetail extends SalesOrderListItem {
  warehouse_id: number;
  warehouse_name: string;
  total_amount: string;
  discount_amount: string;
  remark: string | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  updated_at: string;
  items: SalesOrderItem[];
  payments: SalesPayment[];
}

export interface SalesOrderListResponse {
  items: SalesOrderListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SalesShipPayload {
  items: Array<{ item_id: number; quantity: string }>;
  remark?: string | null;
}

export interface SalesPaymentPayload {
  payment_date: string;
  amount: string;
  method: "cash" | "wechat" | "alipay" | "bank" | "other";
  remark?: string | null;
}
