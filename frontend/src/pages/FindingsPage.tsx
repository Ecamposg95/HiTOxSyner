import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { findingsApi, FindingInput } from "../api/findings";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { FINDING_STATUSES, FINDING_TYPES, LEVELS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Finding } from "../types";

const EMPTY: FindingInput = { title: "", description: "", context: "", type: "Finding", area: "", source: "", impact: "Medium", severity: "Medium", evidence: "", recommendation: "", status: "New" };

export function FindingsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const { data, loading, error, reload } = useResource(
    () => findingsApi.list(engagementId, { status: status || undefined, type: type || undefined }),
    [engagementId, status, type],
  );
  const [editing, setEditing] = useState<Finding | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FindingInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const writable = can(user, "write");

  function openCreate() { setEditing(null); setForm(EMPTY); setFormError(null); setOpen(true); }
  function openEdit(f: Finding) {
    if (!writable) return;
    setEditing(f);
    setForm({ title: f.title, description: f.description, context: f.context, type: f.type, area: f.area, source: f.source, impact: f.impact, severity: f.severity, evidence: f.evidence, recommendation: f.recommendation, status: f.status });
    setFormError(null);
    setOpen(true);
  }
  const set = (key: keyof FindingInput) => (value: string) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await findingsApi.update(editing.id, form);
      else await findingsApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function convert() {
    if (!editing) return;
    setBusy(true); setFormError(null);
    try {
      const initiative = await findingsApi.convert(editing.id);
      setOpen(false);
      navigate(`/initiatives/${initiative.id}`);
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader title="Findings" subtitle="Hallazgos, riesgos y oportunidades del diagnóstico" action={writable && <button className="btn btn-primary" onClick={openCreate}>Nuevo finding</button>} />
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="w-48"><Select value={status} onChange={setStatus} options={FINDING_STATUSES} allowEmpty="Todos los estados" /></div>
        <div className="w-48"><Select value={type} onChange={setType} options={FINDING_TYPES} allowEmpty="Todos los tipos" /></div>
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Finding>
          rows={data?.items ?? []}
          onRowClick={writable ? openEdit : undefined}
          empty={<EmptyState title="Sin findings" hint={writable ? "Registra el primer hallazgo del diagnóstico." : undefined} />}
          columns={[
            { key: "title", header: "Finding", render: (f) => <span className="font-medium">{f.title}<span className="block text-xs text-muted">{f.area || "—"}</span></span> },
            { key: "type", header: "Type", render: (f) => f.type },
            { key: "impact", header: "Impact", render: (f) => <StatusBadge value={f.impact} /> },
            { key: "status", header: "Status", render: (f) => <StatusBadge value={f.status} /> },
            { key: "date", header: "Fecha", render: (f) => formatDate(f.found_on), className: "tabular-nums" },
          ]}
        />
      )}
      <FormDrawer
        open={open}
        title={editing ? "Editar finding" : "Nuevo finding"}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={busy}
        error={formError}
        footer={editing && editing.status !== "Converted to Initiative" && (
          <button type="button" className="btn" onClick={convert} disabled={busy}>Convertir a Initiative</button>
        )}
      >
        <Field label="Título"><input className="input" value={form.title ?? ""} onChange={(e) => set("title")(e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type"><Select value={form.type ?? "Finding"} onChange={set("type")} options={FINDING_TYPES} /></Field>
          <Field label="Status"><Select value={form.status ?? "New"} onChange={set("status")} options={FINDING_STATUSES} /></Field>
          <Field label="Impact"><Select value={form.impact ?? "Medium"} onChange={set("impact")} options={LEVELS} /></Field>
          <Field label="Severity"><Select value={form.severity ?? "Medium"} onChange={set("severity")} options={LEVELS} /></Field>
          <Field label="Área"><input className="input" value={form.area ?? ""} onChange={(e) => set("area")(e.target.value)} maxLength={120} /></Field>
          <Field label="Origen"><input className="input" value={form.source ?? ""} onChange={(e) => set("source")(e.target.value)} maxLength={200} /></Field>
        </div>
        <Field label="Descripción"><textarea className="input min-h-[80px]" value={form.description ?? ""} onChange={(e) => set("description")(e.target.value)} /></Field>
        <Field label="Contexto"><textarea className="input min-h-[60px]" value={form.context ?? ""} onChange={(e) => set("context")(e.target.value)} /></Field>
        <Field label="Evidencia"><textarea className="input min-h-[60px]" value={form.evidence ?? ""} onChange={(e) => set("evidence")(e.target.value)} /></Field>
        <Field label="Recomendación Syner"><textarea className="input min-h-[80px]" value={form.recommendation ?? ""} onChange={(e) => set("recommendation")(e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
