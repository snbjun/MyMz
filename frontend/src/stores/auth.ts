import { defineStore } from "pinia";

import { getMeApi, loginApi, logoutApi, type CurrentUser } from "@/api/auth";
import { ACCESS_TOKEN_STORAGE_KEY } from "@/api/http";

interface AuthState {
  token: string;
  user: CurrentUser | null;
  restoring: boolean;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) || "",
    user: null,
    restoring: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    displayName: (state) => state.user?.display_name || state.user?.username || "",
  },
  actions: {
    async login(username: string, password: string) {
      const response = await loginApi({ username, password });
      this.token = response.data.access_token;
      this.user = response.data.user;
      localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, this.token);
    },
    async restore() {
      if (!this.token || this.user) {
        return Boolean(this.user);
      }

      this.restoring = true;
      try {
        const response = await getMeApi();
        this.user = response.data;
        return true;
      } catch {
        this.clearAuth();
        return false;
      } finally {
        this.restoring = false;
      }
    },
    async logout() {
      try {
        if (this.token) {
          await logoutApi();
        }
      } finally {
        this.clearAuth();
      }
    },
    clearAuth() {
      this.token = "";
      this.user = null;
      localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    },
  },
});
