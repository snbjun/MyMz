import { http } from "@/api/http";
import type { CurrentUser } from "@/api/auth";

export type UserRecord = CurrentUser;

export interface UserListResponse {
  items: UserRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserFormPayload {
  username?: string;
  display_name: string;
  password?: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
}

export function listUsers(params: { keyword?: string; page: number; page_size: number }) {
  return http.get<UserListResponse>("/users", { params });
}

export function createUser(payload: Required<UserFormPayload>) {
  return http.post<UserRecord>("/users", payload);
}

export function updateUser(id: number, payload: Omit<UserFormPayload, "username" | "password">) {
  return http.put<UserRecord>(`/users/${id}`, payload);
}

export function deleteUser(id: number) {
  return http.delete<{ success: boolean }>(`/users/${id}`);
}

export function resetUserPassword(id: number, password: string) {
  return http.post<{ success: boolean }>(`/users/${id}/reset-password`, { password });
}

export function toggleUserActive(id: number) {
  return http.post<UserRecord>(`/users/${id}/toggle-active`);
}
