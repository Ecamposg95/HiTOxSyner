import type { DecisionInput } from "../api/decisions";
import type { Decision, Initiative, Meeting } from "../types";
import { formatDateTime } from "../lib/dates";
import { DECISION_STATUSES } from "../lib/labels";
import { Field, Select } from "./Field";

export const EMPTY_DECISION: DecisionInput = { title: "", context: "", alternatives: "", syner_recommendation: "", final_decision: "", owner_name: "", participants: "", decided_on: null, impact: "", status: "Proposed", initiative_id: null, meeting_id: null };

export function decisionToInput(d: Decision): DecisionInput {
  const { title, context, alternatives, syner_recommendation, final_decision, owner_name, participants, decided_on, impact, status, initiative_id, meeting_id } = d;
  return { title, context, alternatives, syner_recommendation, final_decision, owner_name, participants, decided_on, impact, status, initiative_id, meeting_id };
}

export function DecisionForm({ form, onChange, initiatives, meetings }: {
  form: DecisionInput;
  onChange: (next: DecisionInput) => void;
  initiatives: Initiative[];
  meetings?: Meeting[];
}) {
  const set = (key: keyof DecisionInput, value: unknown) => onChange({ ...form, [key]: value });
  const text = (key: keyof DecisionInput, label: string, rows = 2) => (
    <Field label={label}><textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} /></Field>
  );
  return (
    <>
      <Field label="Decisión"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Status"><Select value={form.status ?? "Proposed"} onChange={(v) => set("status", v)} options={DECISION_STATUSES} /></Field>
        <Field label="Fecha de decisión"><input className="input" type="date" value={form.decided_on ?? ""} onChange={(e) => set("decided_on", e.target.value || null)} /></Field>
        <Field label="Owner"><input className="input" value={form.owner_name ?? ""} onChange={(e) => set("owner_name", e.target.value)} maxLength={200} /></Field>
        <Field label="Initiative">
          <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
            <option value="">Sin initiative</option>
            {initiatives.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </Field>
        {meetings && (
          <Field label="Meeting">
            <select className="input" value={form.meeting_id ?? ""} onChange={(e) => set("meeting_id", e.target.value || null)}>
              <option value="">Sin meeting</option>
              {meetings.map((m) => <option key={m.id} value={m.id}>{m.title} · {formatDateTime(m.held_on)}</option>)}
            </select>
          </Field>
        )}
      </div>
      {text("context", "Contexto", 3)}
      {text("alternatives", "Alternativas", 3)}
      {text("syner_recommendation", "Recomendación Syner", 3)}
      {text("final_decision", "Decisión final")}
      {text("participants", "Participantes")}
      {text("impact", "Impacto")}
    </>
  );
}
