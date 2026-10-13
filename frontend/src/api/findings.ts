import { api } from "./client";
import type { Finding, Initiative, Page } from "../types";

export type FindingInput = Partial<Omit<Finding, "id" | "engagement_id" | "created_at" | "updated_at" | "initiative_id">>;

export const findingsApi = {
  list: (engagementId: string, params: { status?: string; type?: string } = {}) =>
    api.get<Page<Finding>>(`/engagements/${engagementId}/findings`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: FindingInput) => api.post<Finding>(`/engagements/${engagementId}/findings`, data).then((r) => r.data),
  update: (id: string, data: FindingInput) => api.patch<Finding>(`/findings/${id}`, data).then((r) => r.data),
  convert: (id: string) => api.post<Initiative>(`/findings/${id}/convert`).then((r) => r.data),
};
