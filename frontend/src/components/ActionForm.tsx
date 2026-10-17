import type { ActionInput } from "../api/actions";
import type { Initiative, User } from "../types";
import { LEVELS } from "../lib/labels";
import { Field, Select } from "./Field";

export const EMPTY_ACTION: ActionInput = { title: "", description: "", owner_name: "", owner_user_id: null, organization_side: "CLIENT", initiative_id: null, due_date: null, priority: "Medium", status: "Open", evidence: "" };

export function ActionForm({ form, onChange, users, initiatives }: {
  form: ActionInput;
  onChange: (next: ActionInput) => void;
  users: User[];
  initiatives: Initiative[];
}) {
  const set = (key: keyof ActionInput, value: unknown) => onChange({ ...form, [key]: value });
  return (
    <>
      <Field label="Acción"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Responsable (usuario)">
          <select className="input" value={form.owner_user_id ?? ""} onChange={(e) => set("owner_user_id", e.target.value || null)}>
            <option value="">Sin usuario</option>
            {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
          </select>
        </Field>
        {!form.owner_user_id && (
          <Field label="Responsable (nombre)"><input className="input" value={form.owner_name ?? ""} onChange={(e) => set("owner_name", e.target.value)} maxLength={200} /></Field>
        )}
        <Field label="Organización"><Select value={form.organization_side ?? "CLIENT"} onChange={(v) => set("organization_side", v)} options={["CLIENT", "SYNER"]} /></Field>
        <Field label="Initiative">
          <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
            <option value="">Sin initiative</option>
            {initiatives.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </Field>
        <Field label="Fecha compromiso"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
        <Field label="Priority"><Select value={form.priority ?? "Medium"} onChange={(v) => set("priority", v)} options={LEVELS} /></Field>
      </div>
      <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
    </>
  );
}
