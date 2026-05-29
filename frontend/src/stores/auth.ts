import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setSession: (tokens: { access: string; refresh: string }, user: User) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

/**
 * Auth store - persists tokens + user to localStorage so the session
 * survives a page refresh. The axios interceptor reads `accessToken`
 * directly from this store on every request.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: (tokens, user) =>
        set({ accessToken: tokens.access, refreshToken: tokens.refresh, user }),
      setAccessToken: (token) => set({ accessToken: token }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "grindmate-auth" },
  ),
);
