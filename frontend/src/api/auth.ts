import { http } from "@/api/http";

export interface CurrentUser {
  id: number;
  username: string;
  display_name: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: CurrentUser;
}

export function loginApi(payload: { username: string; password: string }) {
  return http.post<LoginResponse>("/auth/login", payload);
}

export function getMeApi() {
  return http.get<CurrentUser>("/auth/me");
}

export function logoutApi() {
  return http.post<{ success: boolean }>("/auth/logout");
}
