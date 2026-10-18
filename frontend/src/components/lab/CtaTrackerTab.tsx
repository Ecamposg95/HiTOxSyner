import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { CtaInput, labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import { CTA_STATUSES } from "../../lib/labels";
import type { Cta } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";
import { StatusBadge } from "../StatusBadge";

const EMPTY: CtaInput = {
  participant_id: "", session_id: "", trigger: "", behavior: "", stakeholder: "", evidence_expected: "",
  due_date: null, accountability_partner: "", impact: "", status: "Committed", evidence_notes: "",
};

export function CtaTrackerTab({ engagementId }: { engagementId: string }) {
  const [sessionId, setSessionId] = useState("");
  const [podId, setPodId] = useState("");
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(
    () => labApi.ctas.list(engagementId, { session_id: sessionId || undefined, pod_id: podId || undefined, status: status || undefined }),
    [engagementId, sessionId, podId, status],
  );
  const sessions = useResource(() => labApi.sessions.list(engagementId), [engagementId]);
  const pods = useResource(() => labApi.pods.list(engagementId), [engagementId]);
  const participants = useResource(() => labApi.participants.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<Cta | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<CtaInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const sessionList = sessions.data?.items ?? [];
  const podList = pods.data?.items ?? [];
  const participantList = participants.data?.items ?? [];
  const participantName = (id: string) => participantList.find((p) => p.id === id)?.full_name ?? "—";
  const sessionLabel = (id: string) => {
    const s = sessionList.find((x) => x.id === id);
    return s ? `Sesión ${s.number} · ${s.theme}` : "—";
  };
  const set = (key: keyof CtaInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY, participant_id: participantList.find((p) => p.is_active)?.id ?? "", session_id: sessionId || (sessionList[0]?.id ?? "") });
    setFormError(null); setOpen(true);
  }
  function openEdit(c: Cta) {
    setEditing(c);
    const { participant_id, session_id, trigger, behavior, stakeholder, evidence_expected, due_date, accountability_partner, impact, status: ctaStatus, evidence_notes } = c;
    setForm({ participant_id, session_id, trigger, behavior, stakeholder, evidence_expected, due_date, accountability_partner, impact, status: ctaStatus, evidence_notes });
    setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.ctas.update(editing.id, form);
      else await labApi.ctas.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const text = (key: keyof CtaInput, label: string, rows = 2, required = false) => (
    <Field label={label}>
      <textarea className="input" rows={rows} value={(form[key] as string) ?? ""} onChange={(e) => set(key, e.target.value)} maxLength={10000} required={required} />
    </Field>
  );

  return (
    <>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <select className="input w-56" value={sessionId} onChange={(e) => setSessionId(e.target.value)} aria-label="Filtrar por sesión">
            <option value="">Todas las sesiones</option>
            {sessionList.map((s) => <option key={s.id} value={s.id}>{s.number}. {s.name}</option>)}
          </select>
          <select className="input w-44" value={podId} onChange={(e) => setPodId(e.target.value)} aria-label="Filtrar por pod">
            <option value="">Todos los pods</option>
            {podList.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <div className="w-44"><Select value={status} onChange={setStatus} options={CTA_STATUSES} allowEmpty="Todos los estados" /></div>
        </div>
        <button className="btn btn-primary" onClick={openCreate} disabled={participantList.length === 0 || sessionList.length === 0}>Nuevo CTA</button>
      </div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Cta>
          rows={data?.items ?? []}
          onRowClick={openEdit}
          empty={<EmptyState title="Sin CTAs" hint="Registra el primer Call to Action de una sesión." />}
          columns={[
            { key: "participant", header: "Participante", render: (c) => <span className="font-medium">{participantName(c.participant_id)}<span className="block text-xs font-normal text-muted">{sessionLabel(c.session_id)}</span></span> },
            { key: "behavior", header: "Behavior", render: (c) => <span className="line-clamp-2">{c.behavior}</span> },
            { key: "due", header: "Fecha", render: (c) => formatDate(c.due_date), className: "tabular-nums" },
            { key: "partner", header: "Accountability partner", render: (c) => c.accountability_partner || "—" },
            { key: "status", header: "Status", render: (c) => <StatusBadge value={c.status} /> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Editar CTA" : "Nuevo CTA"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Participante">
            <select className="input" value={form.participant_id ?? ""} onChange={(e) => set("participant_id", e.target.value)} required>
              <option value="">Selecciona…</option>
              {participantList.filter((p) => p.is_active || p.id === form.participant_id).map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
            </select>
          </Field>
          <Field label="Sesión">
            <select className="input" value={form.session_id ?? ""} onChange={(e) => set("session_id", e.target.value)} required>
              <option value="">Selecciona…</option>
              {sessionList.map((s) => <option key={s.id} value={s.id}>{s.number}. {s.name}</option>)}
            </select>
          </Field>
        </div>
        {text("trigger", "Trigger (situación que activa la conducta)")}
        {text("behavior", "Behavior (conducta comprometida)", 3, true)}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Stakeholder"><input className="input" value={form.stakeholder ?? ""} onChange={(e) => set("stakeholder", e.target.value)} maxLength={200} /></Field>
          <Field label="Accountability partner"><input className="input" value={form.accountability_partner ?? ""} onChange={(e) => set("accountability_partner", e.target.value)} maxLength={200} /></Field>
          <Field label="Fecha compromiso"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
          <Field label="Status"><Select value={form.status ?? "Committed"} onChange={(v) => set("status", v)} options={CTA_STATUSES} /></Field>
        </div>
        {text("evidence_expected", "Evidencia esperada")}
        {text("impact", "Impacto esperado")}
        {text("evidence_notes", "Evidencia registrada", 3)}
      </FormDrawer>
    </>
  );
}
