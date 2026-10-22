import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { meetingsApi, MeetingInput } from "../api/meetings";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { useResource } from "../hooks/useResource";
import { formatDateTime, fromDateTimeInput, toDateTimeInput } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Meeting } from "../types";

export const EMPTY_MEETING: MeetingInput = { title: "", held_on: "", participants: "", objective: "", summary: "", discussion: "", next_steps: "" };

export function MeetingForm({ form, onChange }: { form: MeetingInput; onChange: (next: MeetingInput) => void }) {
  const set = (key: keyof MeetingInput, value: unknown) => onChange({ ...form, [key]: value });
  const text = (key: keyof MeetingInput, label: string, rows = 3) => (
    <Field label={label}><textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} /></Field>
  );
  return (
    <>
      <Field label="Título"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
      <Field label="Fecha y hora">
        <input className="input" type="datetime-local" required value={toDateTimeInput(form.held_on)} onChange={(e) => set("held_on", e.target.value ? fromDateTimeInput(e.target.value) : "")} />
      </Field>
      {text("participants", "Participantes", 2)}
      {text("objective", "Objetivo", 2)}
      {text("summary", "Resumen")}
      {text("discussion", "Discusión", 5)}
      {text("next_steps", "Next steps")}
    </>
  );
}

export function MeetingsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const navigate = useNavigate();
  const { data, loading, error, reload } = useResource(() => meetingsApi.list(engagementId), [engagementId]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<MeetingInput>(EMPTY_MEETING);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const writable = can(user, "write");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      const created = await meetingsApi.create(engagementId, form);
      setOpen(false); setForm(EMPTY_MEETING);
      await reload();
      navigate(`/meetings/${created.id}`);
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader eyebrow="Ejecución" title="Meetings" subtitle="Minutas, acuerdos y siguientes pasos" action={writable && <button className="btn btn-primary" onClick={() => { setForm(EMPTY_MEETING); setFormError(null); setOpen(true); }}>Nueva meeting</button>} />
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Meeting>
          rows={data?.items ?? []}
          onRowClick={(m) => navigate(`/meetings/${m.id}`)}
          empty={<EmptyState title="Sin reuniones registradas" hint={writable ? "Registra la primera reunión del engagement." : undefined} />}
          columns={[
            { key: "title", header: "Meeting", render: (m) => <span className="font-medium">{m.title}<span className="block text-xs text-muted">{m.objective || "—"}</span></span> },
            { key: "held", header: "Fecha", render: (m) => formatDateTime(m.held_on), className: "tabular-nums" },
            { key: "participants", header: "Participantes", render: (m) => <span className="text-muted">{m.participants || "—"}</span> },
          ]}
        />
      )}
      <FormDrawer open={open} title="Nueva meeting" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <MeetingForm form={form} onChange={setForm} />
      </FormDrawer>
    </>
  );
}
