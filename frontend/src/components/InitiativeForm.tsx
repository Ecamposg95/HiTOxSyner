import type { InitiativeInput } from "../api/initiatives";
import type { Initiative } from "../types";
import { INITIATIVE_STATUSES, LEVELS } from "../lib/labels";
import { Field, Select } from "./Field";

export const EMPTY_INITIATIVE: InitiativeInput = { name: "", description: "", objective: "", expected_outcome: "", hito_owner: "", area: "", priority: "Medium", status: "Discovery", start_date: null, target_date: null, progress_pct: 0, expected_impact: "", kpis: "", risks: "", dependencies: "" };

export function initiativeToInput(i: Initiative): InitiativeInput {
  const { name, description, objective, expected_outcome, hito_owner, area, priority, status, start_date, target_date, progress_pct, expected_impact, kpis, risks, dependencies } = i;
  return { name, description, objective, expected_outcome, hito_owner, area, priority, status, start_date, target_date, progress_pct, expected_impact, kpis, risks, dependencies };
}

export function InitiativeForm({ form, onChange }: { form: InitiativeInput; onChange: (next: InitiativeInput) => void }) {
  const set = (key: keyof InitiativeInput, value: unknown) => onChange({ ...form, [key]: value });
  const text = (key: keyof InitiativeInput, label: string, rows = 2) => (
    <Field label={label}><textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} /></Field>
  );
  return (
    <>
      <Field label="Nombre"><input className="input" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} required maxLength={200} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Status"><Select value={form.status ?? "Discovery"} onChange={(v) => set("status", v)} options={INITIATIVE_STATUSES} /></Field>
        <Field label="Priority"><Select value={form.priority ?? "Medium"} onChange={(v) => set("priority", v)} options={LEVELS} /></Field>
        <Field label="Owner HiTO"><input className="input" value={form.hito_owner ?? ""} onChange={(e) => set("hito_owner", e.target.value)} maxLength={200} /></Field>
        <Field label="Área"><input className="input" value={form.area ?? ""} onChange={(e) => set("area", e.target.value)} maxLength={120} /></Field>
        <Field label="Fecha inicio"><input className="input" type="date" value={form.start_date ?? ""} onChange={(e) => set("start_date", e.target.value || null)} /></Field>
        <Field label="Target date"><input className="input" type="date" value={form.target_date ?? ""} onChange={(e) => set("target_date", e.target.value || null)} /></Field>
        <Field label="Progreso (%)"><input className="input" type="number" min={0} max={100} value={form.progress_pct ?? 0} onChange={(e) => set("progress_pct", Number(e.target.value))} /></Field>
      </div>
      {text("description", "Descripción")}
      {text("objective", "Objective")}
      {text("expected_outcome", "Expected Outcome")}
      {text("expected_impact", "Impacto esperado")}
      {text("kpis", "KPIs")}
      {text("risks", "Riesgos")}
      {text("dependencies", "Dependencias")}
    </>
  );
}
