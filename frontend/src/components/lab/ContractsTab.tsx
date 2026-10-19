import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { ContractInput, labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import { CONTRACT_STATUSES } from "../../lib/labels";
import type { ActionContract } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";
import { StatusBadge } from "../StatusBadge";

const EMPTY: ContractInput = { participant_id: "", start_date: null, review_30_date: null, review_60_date: null, success_signal: "", status: "Draft", cta_ids: [] };
const MAX_CTAS = 3;

export function ContractsTab({ engagementId }: { engagementId: string }) {
  const [status, setStatus] = useState("");
  const contracts = useResource(() => labApi.contracts.list(engagementId), [engagementId]);
  const participants = useResource(() => labApi.participants.list(engagementId), [engagementId]);
  const ctas = useResource(() => labApi.ctas.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<ActionContract | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ContractInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const all = contracts.data?.items ?? [];
  const rows = status ? all.filter((c) => c.status === status) : all;
  const participantList = participants.data?.items ?? [];
  const ctaList = ctas.data?.items ?? [];
  const participantName = (id: string) => participantList.find((p) => p.id === id)?.full_name ?? "—";
  const withContract = new Set(all.map((c) => c.participant_id));
  const selectable = participantList.filter((p) => (p.is_active && !withContract.has(p.id)) || p.id === editing?.participant_id);
  const participantCtas = ctaList.filter((c) => c.participant_id === form.participant_id);
  const selected = form.cta_ids ?? [];
  const set = (key: keyof ContractInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() { setEditing(null); setForm({ ...EMPTY, participant_id: selectable[0]?.id ?? "" }); setFormError(null); setOpen(true); }
  function openEdit(c: ActionContract) {
    setEditing(c);
    setForm({ participant_id: c.participant_id, start_date: c.start_date, review_30_date: c.review_30_date, review_60_date: c.review_60_date, success_signal: c.success_signal, status: c.status, cta_ids: c.cta_ids });
    setFormError(null); setOpen(true);
  }
  function changeParticipant(id: string) { setForm((f) => ({ ...f, participant_id: id, cta_ids: [] })); }
  function toggleCta(id: string) { set("cta_ids", selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]); }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.contracts.update(editing.id, form);
      else await labApi.contracts.create(engagementId, form);
      setOpen(false);
      await contracts.reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="w-48"><Select value={status} onChange={setStatus} options={CONTRACT_STATUSES} allowEmpty="Todos los estados" /></div>
        <button className="btn btn-primary" onClick={openCreate} disabled={selectable.length === 0}>Nuevo contract</button>
      </div>
      {contracts.error && <p className="mb-4 text-sm text-danger">{contracts.error}</p>}
      {contracts.loading && !contracts.data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<ActionContract>
          rows={rows}
          onRowClick={openEdit}
          empty={<EmptyState title="Sin Leadership Action Contracts" hint="Cada participante firma un contrato con hasta 3 CTAs." />}
          columns={[
            { key: "participant", header: "Participante", render: (c) => <span className="font-medium">{participantName(c.participant_id)}<span className="line-clamp-1 block text-xs font-normal text-muted">{c.success_signal || "Sin señal de éxito"}</span></span> },
            { key: "start", header: "Inicio", render: (c) => formatDate(c.start_date), className: "tabular-nums" },
            { key: "r30", header: "Revisión +30", render: (c) => formatDate(c.review_30_date), className: "tabular-nums" },
            { key: "r60", header: "Revisión +60", render: (c) => formatDate(c.review_60_date), className: "tabular-nums" },
            { key: "ctas", header: "CTAs", render: (c) => <span className="tabular-nums">{c.cta_ids.length}/{MAX_CTAS}</span> },
            { key: "status", header: "Status", render: (c) => <StatusBadge value={c.status} /> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Editar Leadership Action Contract" : "Nuevo Leadership Action Contract"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Participante">
          <select className="input" value={form.participant_id ?? ""} onChange={(e) => changeParticipant(e.target.value)} required>
            <option value="">Selecciona…</option>
            {selectable.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Inicio"><input className="input" type="date" value={form.start_date ?? ""} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value || null, review_30_date: null, review_60_date: null }))} /></Field>
          <Field label="Status"><Select value={form.status ?? "Draft"} onChange={(v) => set("status", v)} options={CONTRACT_STATUSES} /></Field>
          <Field label="Revisión +30 (se recalcula al cambiar el inicio si se deja vacía)"><input className="input" type="date" value={form.review_30_date ?? ""} onChange={(e) => set("review_30_date", e.target.value || null)} /></Field>
          <Field label="Revisión +60 (se recalcula al cambiar el inicio si se deja vacía)"><input className="input" type="date" value={form.review_60_date ?? ""} onChange={(e) => set("review_60_date", e.target.value || null)} /></Field>
        </div>
        <Field label="Señal de éxito"><textarea className="input" rows={3} value={form.success_signal ?? ""} onChange={(e) => set("success_signal", e.target.value)} maxLength={10000} /></Field>
        <fieldset>
          <legend className="label">CTAs del contrato ({selected.length}/{MAX_CTAS})</legend>
          {participantCtas.length === 0 ? <p className="text-sm text-muted">Este participante no tiene CTAs registrados.</p> : (
            <ul className="space-y-2">
              {participantCtas.map((c) => {
                const checked = selected.includes(c.id);
                return (
                  <li key={c.id}>
                    <label className={`flex items-start gap-2 text-sm ${!checked && selected.length >= MAX_CTAS ? "text-muted" : ""}`}>
                      <input type="checkbox" className="mt-1" checked={checked} disabled={!checked && selected.length >= MAX_CTAS} onChange={() => toggleCta(c.id)} />
                      <span className="flex-1">{c.behavior}</span>
                      <StatusBadge value={c.status} />
                    </label>
                  </li>
                );
              })}
            </ul>
          )}
        </fieldset>
      </FormDrawer>
    </>
  );
}
