import axios from "axios";

const STORAGE_KEY = "ai-copilot-api-base";

export const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  if (typeof window === "undefined") return envUrl;
  return localStorage.getItem(STORAGE_KEY) || envUrl;
};

export const setApiBaseUrl = (url: string) => {
  localStorage.setItem(STORAGE_KEY, url);
  apiClient.defaults.baseURL = url;
};

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 0,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("ai-copilot-token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      // UI-only auth: do nothing automatic for now
    }
    return Promise.reject(error);
  },
);
