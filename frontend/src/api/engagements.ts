import { api } from "./client";
import type { Dashboard, Engagement, User } from "../types";

export const engagementsApi = {
  list: () => api.get<Engagement[]>("/engagements").then((r) => r.data),
  get: (id: string) => api.get<Engagement>(`/engagements/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<Engagement>) => api.patch<Engagement>(`/engagements/${id}`, data).then((r) => r.data),
  users: (id: string) => api.get<User[]>(`/engagements/${id}/users`).then((r) => r.data),
  dashboard: (id: string) => api.get<Dashboard>(`/engagements/${id}/dashboard`).then((r) => r.data),
};
