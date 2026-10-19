import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { decisionsApi, DecisionInput } from "../api/decisions";
import { initiativesApi } from "../api/initiatives";
import { meetingsApi } from "../api/meetings";
import { Prose } from "../components/Block";
import { DataTable } from "../components/DataTable";
import { DecisionForm, EMPTY_DECISION, decisionToInput } from "../components/DecisionForm";
import { EmptyState } from "../components/EmptyState";
import { Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { DECISION_STATUSES, RESOLUTION_STATUSES } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Decision, DecisionStatus } from "../types";

export function DecisionsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(() => decisionsApi.list(engagementId, { status: status || undefined }), [engagementId, status]);
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const meetings = useResource(() => meetingsApi.list(engagementId), [engagementId]);
  const writable = can(user, "write");
  const approver = can(user, "approveDecision");
  const [selected, setSelected] = useState<Decision | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<DecisionInput>(EMPTY_DECISION);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreate() { setSelected(null); setForm(EMPTY_DECISION); setFormError(null); setOpen(true); }
  function openRow(d: Decision) {
    if (!writable && !approver) return;
    setSelected(d); setForm(decisionToInput(d)); setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!writable) return;
    setBusy(true); setFormError(null);
    try {
      if (selected) await decisionsApi.update(selected.id, form);
      else await decisionsApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function resolve(next: DecisionStatus) {
    if (!selected) return;
    setBusy(true); setFormError(null);
    try {
      await decisionsApi.update(selected.id, { status: next });
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const initiativeName = (id: string | null) => initiatives.data?.items.find((i) => i.id === id)?.name ?? "—";
  const pending = !!selected && (selected.status === "Proposed" || selected.status === "Under Review");
  const resolutionButtons = selected && approver && pending && (
    <>
      {RESOLUTION_STATUSES.map((s) => (
        <button key={s} type="button" className={`btn ${s === "Approved" ? "btn-primary" : ""}`} disabled={busy} onClick={() => resolve(s)}>{s}</button>
      ))}
    </>
  );

  return (
    <>
      <PageHeader title="Decision Log" subtitle="Decisiones estratégicas con contexto, alternativas y recomendación Syner" action={writable && <button className="btn btn-primary" onClick={openCreate}>Nueva decision</button>} />
      <div className="mb-4 w-48"><Select value={status} onChange={setStatus} options={DECISION_STATUSES} allowEmpty="Todos los estados" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Decision>
          rows={data?.items ?? []}
          onRowClick={writable || approver ? openRow : undefined}
          empty={<EmptyState title="Sin decisiones registradas" hint={writable ? "Registra la primera decisión del engagement." : undefined} />}
          columns={[
            { key: "title", header: "Decision", render: (d) => <span className="font-medium">{d.title}<span className="block text-xs text-muted">{initiativeName(d.initiative_id)}</span></span> },
            { key: "owner", header: "Owner", render: (d) => d.owner_name || "—" },
            { key: "status", header: "Status", render: (d) => <StatusBadge value={d.status} /> },
            { key: "decided", header: "Decidida", render: (d) => formatDate(d.decided_on), className: "tabular-nums" },
          ]}
        />
      )}
      <FormDrawer
        open={open}
        title={selected ? (writable ? "Editar decision" : "Decision") : "Nueva decision"}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={busy}
        error={formError}
        hideSubmit={!writable}
        footer={resolutionButtons}
      >
        {writable ? (
          <DecisionForm form={form} onChange={setForm} initiatives={initiatives.data?.items ?? []} meetings={meetings.data?.items ?? []} />
        ) : selected && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold">{selected.title}</h3>
              <div className="mt-1 flex items-center gap-2 text-xs text-muted"><StatusBadge value={selected.status} /><span>Owner: {selected.owner_name || "—"}</span></div>
            </div>
            <Prose label="Contexto" text={selected.context} />
            <Prose label="Alternativas" text={selected.alternatives} />
            <Prose label="Recomendación Syner" text={selected.syner_recommendation} />
            <Prose label="Decisión final" text={selected.final_decision} />
            <Prose label="Impacto" text={selected.impact} />
          </div>
        )}
      </FormDrawer>
    </>
  );
}
