import { api } from "./client";
import type { Document, DocumentLink, Page } from "../types";

export type DocumentInput = Partial<Omit<Document, "id" | "engagement_id" | "uploader_id" | "links" | "created_at" | "updated_at">>;

export const documentsApi = {
  list: (engagementId: string, params: { category?: string } = {}) =>
    api.get<Page<Document>>(`/engagements/${engagementId}/documents`, { params: { ...params, limit: 200 } }).then((r) => r.data),
  create: (engagementId: string, data: DocumentInput) => api.post<Document>(`/engagements/${engagementId}/documents`, data).then((r) => r.data),
  update: (id: string, data: DocumentInput) => api.patch<Document>(`/documents/${id}`, data).then((r) => r.data),
  addLink: (id: string, data: { entity_type: string; entity_id: string }) => api.post<DocumentLink>(`/documents/${id}/links`, data).then((r) => r.data),
  removeLink: (id: string, linkId: string) => api.delete<void>(`/documents/${id}/links/${linkId}`).then(() => undefined),
};
