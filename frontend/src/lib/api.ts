import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/stores/auth";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/**
 * Axios instance used for every backend call.
 *
 * Request interceptor attaches the JWT bearer token from the auth store.
 * Response interceptor refreshes once on 401, then retries the original request.
 * If refresh fails, we clear the session and let the route guard redirect.
 */
export const api = axios.create({
  baseURL: BASE_URL,
  // 30s default covers Render free-tier cold start (~30s after 15min idle).
  // Slow endpoints (LeetCode sync) can override per-call via { timeout: 60_000 }.
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) return null;

  try {
    const { data } = await axios.post<{ access: string; refresh?: string }>(
      `${BASE_URL}/auth/token/refresh/`,
      { refresh },
      { timeout: 10_000 },
    );
    useAuthStore.getState().setAccessToken(data.access);
    if (data.refresh) {
      // simplejwt rotates by default - keep the new refresh token
      useAuthStore.setState({ refreshToken: data.refresh });
    }
    return data.access;
  } catch {
    useAuthStore.getState().logout();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    if (!original || error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    // Don't try to refresh if this *was* the refresh call.
    if (original.url?.includes("/auth/token/refresh")) {
      useAuthStore.getState().logout();
      return Promise.reject(error);
    }

    original._retry = true;
    refreshInFlight ??= refreshAccessToken().finally(() => {
      refreshInFlight = null;
    });
    const newToken = await refreshInFlight;
    if (!newToken) return Promise.reject(error);

    original.headers.Authorization = `Bearer ${newToken}`;
    return api(original);
  },
);
