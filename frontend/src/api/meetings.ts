import { api } from "./client";
import type { ActionInput } from "./actions";
import type { DecisionInput } from "./decisions";
import type { Action, Decision, Meeting, MeetingDetail, Page } from "../types";

export type MeetingInput = Partial<Omit<Meeting, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const meetingsApi = {
  list: (engagementId: string) => api.get<Page<Meeting>>(`/engagements/${engagementId}/meetings`, { params: { limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: MeetingInput) => api.post<Meeting>(`/engagements/${engagementId}/meetings`, data).then((r) => r.data),
  update: (id: string, data: MeetingInput) => api.patch<Meeting>(`/meetings/${id}`, data).then((r) => r.data),
  detail: (id: string) => api.get<MeetingDetail>(`/meetings/${id}/detail`).then((r) => r.data),
  createAction: (id: string, data: ActionInput) => api.post<Action>(`/meetings/${id}/actions`, data).then((r) => r.data),
  createDecision: (id: string, data: DecisionInput) => api.post<Decision>(`/meetings/${id}/decisions`, data).then((r) => r.data),
};
