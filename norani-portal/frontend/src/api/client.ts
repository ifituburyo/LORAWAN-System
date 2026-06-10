import axios, { AxiosError } from "axios";

const API_BASE = (import.meta.env.VITE_API_BASE as string) || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: false,
});

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("norani_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("norani_token");
      localStorage.removeItem("norani_user");
      // Avoid infinite loop if already on login page
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

/**
 * Helper to extract a user-friendly error message from an Axios error.
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; errors?: Array<{ message: string }> };
    if (data?.detail) return data.detail;
    if (data?.errors && data.errors.length > 0) {
      return data.errors.map((e) => e.message).join(", ");
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unknown error occurred";
}
