import { api } from "./client";
import type { Milestone, Page } from "../types";

export type MilestoneInput = Partial<Omit<Milestone, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const milestonesApi = {
  list: (engagementId: string, params: { phase?: string; status?: string; initiative_id?: string } = {}) =>
    api.get<Page<Milestone>>(`/engagements/${engagementId}/milestones`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: MilestoneInput) => api.post<Milestone>(`/engagements/${engagementId}/milestones`, data).then((r) => r.data),
  update: (id: string, data: MilestoneInput) => api.patch<Milestone>(`/milestones/${id}`, data).then((r) => r.data),
};
