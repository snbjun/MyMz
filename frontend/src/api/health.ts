import { http } from "@/api/http";

export interface HealthResponse {
  status: string;
  service: string;
}

export function getHealth() {
  return http.get<HealthResponse>("/health");
}
