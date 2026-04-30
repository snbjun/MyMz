export interface SalesSummary {
  order_count: number;
  total_quantity: string;
  receivable_amount: string;
  paid_amount: string;
  unpaid_amount: string;
}

export interface PurchaseSummary {
  order_count: number;
  total_quantity: string;
  payable_amount: string;
  paid_amount: string;
  unpaid_amount: string;
}

export interface ReceivableSummary {
  customer_count: number;
  total_receivable: string;
}

export interface PayableSummary {
  supplier_count: number;
  total_payable: string;
}

export interface InventorySummary {
  product_count: number;
  total_quantity: string;
  total_cost: string;
  low_stock_count: number;
}

export interface InventoryMovementTypeItem {
  movement_type: string;
  direction: string;
  quantity: string;
  amount: string;
}

export interface InventoryMovementSummary {
  in_quantity: string;
  out_quantity: string;
  in_amount: string;
  out_amount: string;
  items: InventoryMovementTypeItem[];
}

export interface FinanceAccountBalanceItem {
  account_id: number;
  account_name: string;
  account_type: string;
  opening_balance: string;
  current_balance: string;
}

export interface FinanceSummary {
  account_count: number;
  balance_total: string;
  income_amount: string;
  expense_amount: string;
  net_amount: string;
  accounts: FinanceAccountBalanceItem[];
}

export interface ProfitSummary {
  sales_amount: string;
  purchase_amount: string;
  gross_profit: string;
  income_amount: string;
  expense_amount: string;
  finance_net_amount: string;
  estimated_net_profit: string;
}

export interface OverviewReport {
  start_date: string;
  end_date: string;
  sales_summary: SalesSummary;
  purchase_summary: PurchaseSummary;
  receivable_summary: ReceivableSummary;
  payable_summary: PayableSummary;
  inventory_summary: InventorySummary;
  finance_summary: FinanceSummary;
  profit_summary: ProfitSummary;
}

export interface SalesByCustomerItem {
  customer_id: number;
  customer_name: string;
  order_count: number;
  sales_amount: string;
  paid_amount: string;
  unpaid_amount: string;
}

export interface SalesByProductItem {
  product_id: number;
  product_code: string | null;
  product_name: string;
  quantity: string;
  sales_amount: string;
}

export interface PurchaseBySupplierItem {
  supplier_id: number;
  supplier_name: string;
  order_count: number;
  purchase_amount: string;
  paid_amount: string;
  unpaid_amount: string;
}

export interface PurchaseByProductItem {
  product_id: number;
  product_code: string | null;
  product_name: string;
  quantity: string;
  purchase_amount: string;
}

export interface ReceivableItem {
  customer_id: number;
  customer_code: string | null;
  customer_name: string;
  phone: string | null;
  current_receivable: string;
}

export interface PayableItem {
  supplier_id: number;
  supplier_code: string | null;
  supplier_name: string;
  phone: string | null;
  current_payable: string;
}

export interface FinanceByCategoryItem {
  category_id: number;
  category_name: string;
  type: string;
  amount: string;
}

export interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
