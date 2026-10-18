import { api } from "./client";
import type { ActionContract, Cta, LabSession, LabSummary, Page, Participant, Pod } from "../types";

type Input<T> = Partial<Omit<T, "id" | "engagement_id" | "created_at" | "updated_at">>;
export type LabSessionInput = Input<LabSession>;
export type PodInput = Input<Pod>;
export type ParticipantInput = Input<Participant>;
export type CtaInput = Input<Cta>;
export type ContractInput = Input<ActionContract>;

function resource<T, I>(segment: string) {
  return {
    list: (engagementId: string, params: Record<string, string | undefined> = {}) =>
      api.get<Page<T>>(`/engagements/${engagementId}/lab/${segment}`, { params: { ...params, limit: 200 } }).then((r) => r.data),
    create: (engagementId: string, data: I) => api.post<T>(`/engagements/${engagementId}/lab/${segment}`, data).then((r) => r.data),
    update: (id: string, data: I) => api.patch<T>(`/lab/${segment}/${id}`, data).then((r) => r.data),
  };
}

export const labApi = {
  sessions: resource<LabSession, LabSessionInput>("sessions"),
  pods: resource<Pod, PodInput>("pods"),
  participants: resource<Participant, ParticipantInput>("participants"),
  ctas: resource<Cta, CtaInput>("ctas"),
  contracts: resource<ActionContract, ContractInput>("contracts"),
  summary: (engagementId: string) => api.get<LabSummary>(`/engagements/${engagementId}/lab/summary`).then((r) => r.data),
};
