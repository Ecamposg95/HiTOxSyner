import { api } from "./client";
import type { Comment, Page } from "../types";

export const commentsApi = {
  list: (engagementId: string, entityType: string, entityId: string) =>
    api.get<Page<Comment>>(`/engagements/${engagementId}/comments`, { params: { entity_type: entityType, entity_id: entityId, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: { entity_type: string; entity_id: string; body: string }) =>
    api.post<Comment>(`/engagements/${engagementId}/comments`, data).then((r) => r.data),
};
