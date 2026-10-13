import { api } from "./client";
import type { Action, Page } from "../types";

export type ActionInput = Partial<Omit<Action, "id" | "engagement_id" | "created_at" | "updated_at">>;

export const actionsApi = {
  list: (engagementId: string, params: { status?: string; initiative_id?: string; mine?: boolean } = {}) =>
    api.get<Page<Action>>(`/engagements/${engagementId}/actions`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: ActionInput) => api.post<Action>(`/engagements/${engagementId}/actions`, data).then((r) => r.data),
  update: (id: string, data: ActionInput) => api.patch<Action>(`/actions/${id}`, data).then((r) => r.data),
};
