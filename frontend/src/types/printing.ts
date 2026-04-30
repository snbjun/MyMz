export type PrintDocType = "sales_order" | "purchase_order";

export interface PrintSetting {
  id: number;
  doc_type: PrintDocType;
  template_name: string;
  paper_size: "A4";
  show_company_name: boolean;
  company_name: string | null;
  show_contact: boolean;
  contact_text: string | null;
  show_amount: boolean;
  show_unit_price: boolean;
  show_discount: boolean;
  show_remark: boolean;
  show_signature: boolean;
  footer_text: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export type PrintSettingPayload = Partial<
  Pick<
    PrintSetting,
    | "template_name"
    | "paper_size"
    | "show_company_name"
    | "company_name"
    | "show_contact"
    | "contact_text"
    | "show_amount"
    | "show_unit_price"
    | "show_discount"
    | "show_remark"
    | "show_signature"
    | "footer_text"
  >
>;

export interface PrintItem {
  id: number;
  product_code: string | null;
  product_name: string;
  product_barcode: string | null;
  product_spec: string | null;
  product_model: string | null;
  unit_name: string | null;
  quantity: string;
  unit_price: string;
  discount_amount: string;
  line_amount: string;
  remark: string | null;
}

export interface PrintPaymentSummary {
  count: number;
  amount: string;
}

export interface SalesOrderPrintData {
  order_no: string;
  order_date: string;
  status: string;
  customer_name: string;
  customer_phone: string | null;
  customer_address: string | null;
  warehouse_name: string;
  items: PrintItem[];
  total_quantity: string;
  total_amount: string;
  discount_amount: string;
  receivable_amount: string;
  paid_amount: string;
  unpaid_amount: string;
  remark: string | null;
  created_by_name: string | null;
  confirmed_at: string | null;
  payment_summary: PrintPaymentSummary;
  print_settings: PrintSetting;
}

export interface PurchaseOrderPrintData {
  order_no: string;
  order_date: string;
  status: string;
  supplier_name: string;
  supplier_phone: string | null;
  supplier_address: string | null;
  warehouse_name: string;
  items: PrintItem[];
  total_quantity: string;
  total_amount: string;
  discount_amount: string;
  payable_amount: string;
  paid_amount: string;
  unpaid_amount: string;
  remark: string | null;
  created_by_name: string | null;
  confirmed_at: string | null;
  payment_summary: PrintPaymentSummary;
  print_settings: PrintSetting;
}

