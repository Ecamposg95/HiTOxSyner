import { create } from "zustand";
import { authApi } from "../api/auth";
import { setUnauthorizedHandler } from "../api/client";
import { useEngagementStore } from "./engagement";
import type { User } from "../types";

type Status = "unknown" | "anonymous" | "authenticated";

interface AuthState {
  user: User | null;
  status: Status;
  bootstrap: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "unknown",
  async bootstrap() {
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated" });
    } catch {
      set({ user: null, status: "anonymous" });
    }
  },
  async login(email, password) {
    const result = await authApi.login(email, password);
    set({ user: result.user, status: "authenticated" });
  },
  async logout() {
    await authApi.logout();
    useEngagementStore.getState().reset();
    set({ user: null, status: "anonymous" });
  },
}));

setUnauthorizedHandler(() => {
  useEngagementStore.getState().reset();
  useAuthStore.setState({ user: null, status: "anonymous" });
});
