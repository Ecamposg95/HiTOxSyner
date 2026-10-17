import { api } from "./client";
import type { Decision, Page } from "../types";

export type DecisionInput = Partial<Omit<Decision, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const decisionsApi = {
  list: (engagementId: string, params: { status?: string; initiative_id?: string; meeting_id?: string } = {}) =>
    api.get<Page<Decision>>(`/engagements/${engagementId}/decisions`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: DecisionInput) => api.post<Decision>(`/engagements/${engagementId}/decisions`, data).then((r) => r.data),
  update: (id: string, data: DecisionInput) => api.patch<Decision>(`/decisions/${id}`, data).then((r) => r.data),
};
