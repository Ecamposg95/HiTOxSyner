import { api } from "./client";
import type { Initiative, InitiativeDetail, Page } from "../types";

export type InitiativeInput = Partial<Omit<Initiative, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const initiativesApi = {
  list: (engagementId: string, params: { status?: string } = {}) =>
    api.get<Page<Initiative>>(`/engagements/${engagementId}/initiatives`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: InitiativeInput) => api.post<Initiative>(`/engagements/${engagementId}/initiatives`, data).then((r) => r.data),
  update: (id: string, data: InitiativeInput) => api.patch<Initiative>(`/initiatives/${id}`, data).then((r) => r.data),
  detail: (id: string) => api.get<InitiativeDetail>(`/initiatives/${id}/detail`).then((r) => r.data),
};
