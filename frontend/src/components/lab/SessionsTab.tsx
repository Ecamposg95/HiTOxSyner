import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { labApi, LabSessionInput } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import { LAB_SESSION_CATALOG, LAB_SESSION_STATUSES } from "../../lib/labels";
import type { LabSession } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";
import { StatusBadge } from "../StatusBadge";

const EMPTY: LabSessionInput = { number: 1, held_on: null, status: "Planned", attendance_count: null, syner_notes: "" };

export function SessionsTab({ engagementId }: { engagementId: string }) {
  const { data, loading, error, reload } = useResource(() => labApi.sessions.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<LabSession | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<LabSessionInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const items = data?.items ?? [];
  const used = new Set(items.map((s) => s.number));
  const available = LAB_SESSION_CATALOG.filter((c) => !used.has(c.number));
  const set = (key: keyof LabSessionInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() { setEditing(null); setForm({ ...EMPTY, number: available[0]?.number ?? 1 }); setFormError(null); setOpen(true); }
  function openEdit(s: LabSession) {
    setEditing(s);
    setForm({ held_on: s.held_on, status: s.status, attendance_count: s.attendance_count, syner_notes: s.syner_notes });
    setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.sessions.update(editing.id, form);
      else await labApi.sessions.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">Cuatro sesiones del programa: DECIDIR, CONFRONTAR, ALINEAR y TRANSFORMAR.</p>
        {available.length > 0 && <button className="btn btn-primary" onClick={openCreate}>Nueva sesión</button>}
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<LabSession>
          rows={items}
          onRowClick={openEdit}
          empty={<EmptyState title="Sin sesiones" hint="Programa la primera sesión del Lab." />}
          columns={[
            { key: "number", header: "#", render: (s) => <span className="tabular-nums">{s.number}</span> },
            { key: "name", header: "Sesión", render: (s) => <span className="font-medium">{s.name}<span className="block text-xs font-normal text-muted">{s.theme}</span></span> },
            { key: "date", header: "Fecha", render: (s) => formatDate(s.held_on), className: "tabular-nums" },
            { key: "status", header: "Status", render: (s) => <StatusBadge value={s.status} /> },
            { key: "attendance", header: "Asistencia", render: (s) => <span className="tabular-nums">{s.attendance_count ?? "—"}</span> },
            { key: "notes", header: "Notas Syner", render: (s) => <span className="line-clamp-2 text-xs text-muted">{s.syner_notes || "—"}</span> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? `Sesión ${editing.number} · ${editing.name}` : "Nueva sesión"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        {!editing && (
          <Field label="Sesión">
            <select className="input" value={form.number ?? 1} onChange={(e) => set("number", Number(e.target.value))}>
              {available.map((c) => <option key={c.number} value={c.number}>{c.number}. {c.name} · {c.theme}</option>)}
            </select>
          </Field>
        )}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Fecha"><input className="input" type="date" value={form.held_on ?? ""} onChange={(e) => set("held_on", e.target.value || null)} /></Field>
          <Field label="Status"><Select value={form.status ?? "Planned"} onChange={(v) => set("status", v)} options={LAB_SESSION_STATUSES} /></Field>
          <Field label="Asistencia"><input className="input" type="number" min={0} value={form.attendance_count ?? ""} onChange={(e) => set("attendance_count", e.target.value === "" ? null : Number(e.target.value))} /></Field>
        </div>
        <Field label="Notas Syner (solo equipo Syner)"><textarea className="input" rows={4} value={form.syner_notes ?? ""} onChange={(e) => set("syner_notes", e.target.value)} maxLength={10000} /></Field>
      </FormDrawer>
    </>
  );
}
