import { http } from "@/api/http";
import type {
  ProductCategory,
  ProductListResponse,
  ProductPayload,
  ProductRecord,
  ProductUnit,
} from "@/types/product";

export interface ProductListParams {
  keyword?: string;
  category_id?: number;
  unit_id?: number;
  is_active?: boolean;
  page: number;
  page_size: number;
}

export function listProductCategories() {
  return http.get<ProductCategory[]>("/product-categories");
}

export function createProductCategory(payload: { name: string; sort_order: number; is_default: boolean }) {
  return http.post<ProductCategory>("/product-categories", payload);
}

export function updateProductCategory(
  id: number,
  payload: { name: string; sort_order: number; is_default: boolean },
) {
  return http.put<ProductCategory>(`/product-categories/${id}`, payload);
}

export function deleteProductCategory(id: number) {
  return http.delete<{ success: boolean }>(`/product-categories/${id}`);
}

export function listProductUnits() {
  return http.get<ProductUnit[]>("/product-units");
}

export function createProductUnit(payload: { name: string; sort_order: number; is_default: boolean }) {
  return http.post<ProductUnit>("/product-units", payload);
}

export function updateProductUnit(id: number, payload: { name: string; sort_order: number; is_default: boolean }) {
  return http.put<ProductUnit>(`/product-units/${id}`, payload);
}

export function deleteProductUnit(id: number) {
  return http.delete<{ success: boolean }>(`/product-units/${id}`);
}

export function listProducts(params: ProductListParams) {
  return http.get<ProductListResponse>("/products", { params });
}

export function getProduct(id: number) {
  return http.get<ProductRecord>(`/products/${id}`);
}

export function createProduct(payload: ProductPayload) {
  return http.post<ProductRecord>("/products", payload);
}

export function updateProduct(id: number, payload: ProductPayload) {
  return http.put<ProductRecord>(`/products/${id}`, payload);
}

export function deleteProduct(id: number) {
  return http.delete<{ success: boolean }>(`/products/${id}`);
}

export function toggleProductActive(id: number) {
  return http.post<ProductRecord>(`/products/${id}/toggle-active`);
}
