import { api } from "./client";
import type { User } from "../types";

export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; user: User }>("/auth/login", { email, password }).then((r) => r.data),
  logout: () => api.post("/auth/logout").then(() => undefined),
  me: () => api.get<User>("/auth/me").then((r) => r.data),
};
