import axios from "axios";

export const ACCESS_TOKEN_STORAGE_KEY = "mymz_access_token";

export const http = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    }
    return Promise.reject(error);
  },
);
