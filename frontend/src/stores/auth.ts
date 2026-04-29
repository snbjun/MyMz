import { defineStore } from "pinia";

interface AuthState {
  isLoggedIn: boolean;
  username: string;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    isLoggedIn: false,
    username: "",
  }),
  actions: {
    login(username: string) {
      this.isLoggedIn = true;
      this.username = username;
    },
    logout() {
      this.isLoggedIn = false;
      this.username = "";
    },
  },
});
