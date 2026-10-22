import { FormEvent, useState } from "react";
import { errorMessage } from "../../api/client";
import { labApi, ParticipantInput } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import type { Participant } from "../../types";
import { DataTable } from "../DataTable";
import { EmptyState } from "../EmptyState";
import { Field, Select } from "../Field";
import { FormDrawer } from "../FormDrawer";

const EMPTY: ParticipantInput = { full_name: "", area: "", title: "", pod_id: null, is_active: true };

export function ParticipantsTab({ engagementId }: { engagementId: string }) {
  const participants = useResource(() => labApi.participants.list(engagementId), [engagementId]);
  const pods = useResource(() => labApi.pods.list(engagementId), [engagementId]);
  const [editing, setEditing] = useState<Participant | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ParticipantInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);
  const [newPodName, setNewPodName] = useState("");
  const [podError, setPodError] = useState<string | null>(null);

  const rows = participants.data?.items ?? [];
  const podList = pods.data?.items ?? [];
  const set = (key: keyof ParticipantInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  function openCreate() { setEditing(null); setForm(EMPTY); setFormError(null); setOpen(true); }
  function openEdit(p: Participant) {
    setEditing(p);
    setForm({ full_name: p.full_name, area: p.area, title: p.title, pod_id: p.pod_id, is_active: p.is_active });
    setFormError(null); setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await labApi.participants.update(editing.id, form);
      else await labApi.participants.create(engagementId, form);
      setOpen(false);
      await participants.reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  async function assignPod(p: Participant, podId: string | null) {
    setRowError(null);
    try {
      await labApi.participants.update(p.id, { pod_id: podId });
      await participants.reload();
    } catch (err) { setRowError(errorMessage(err)); }
  }

  async function addPod(e: FormEvent) {
    e.preventDefault();
    const name = newPodName.trim();
    if (!name) return;
    setPodError(null);
    try {
      await labApi.pods.create(engagementId, { number: Math.max(0, ...podList.map((p) => p.number)) + 1, name });
      setNewPodName("");
      await pods.reload();
    } catch (err) { setPodError(errorMessage(err)); }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <div className="mb-4 flex items-center justify-between gap-3">
          <p className="text-sm text-muted">{rows.filter((p) => p.is_active).length} participantes activos</p>
          <button className="btn btn-primary" onClick={openCreate}>Nuevo participante</button>
        </div>
        {(participants.error || rowError) && <p className="mb-4 text-sm text-danger">{participants.error ?? rowError}</p>}
        {participants.loading && !participants.data ? <p className="text-sm text-muted">Cargando…</p> : (
          <DataTable<Participant>
            rows={rows}
            onRowClick={openEdit}
            empty={<EmptyState title="Sin participantes" hint="Registra a los participantes del Lab." />}
            columns={[
              { key: "name", header: "Participante", render: (p) => (
                <span className="font-medium">
                  <span className={p.is_active ? "" : "text-muted line-through"}>{p.full_name}</span>
                  <span className="block text-xs font-normal text-muted">{p.title || "—"}</span>
                </span>
              ) },
              { key: "area", header: "Área", render: (p) => p.area || "—" },
              { key: "pod", header: "Pod", render: (p) => (
                <select
                  className="input py-1"
                  value={p.pod_id ?? ""}
                  aria-label={`Pod de ${p.full_name}`}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) => assignPod(p, e.target.value || null)}
                >
                  <option value="">Sin pod</option>
                  {podList.map((pod) => <option key={pod.id} value={pod.id}>{pod.name}</option>)}
                </select>
              ) },
              { key: "active", header: "Estado", render: (p) => <span className="text-xs text-muted">{p.is_active ? "Activo" : "Inactivo"}</span> },
            ]}
          />
        )}
      </div>
      <section className="card p-5">
        <h2 className="mb-3 font-display text-[15px] font-medium text-ink">Pods</h2>
        {pods.error && <p className="mb-3 text-sm text-danger">{pods.error}</p>}
        {podList.length === 0 ? <p className="text-sm text-muted">Sin pods.</p> : (
          <ul className="space-y-2">
            {podList.map((pod) => (
              <li key={pod.id} className="flex items-center justify-between text-sm">
                <span>{pod.number}. {pod.name}</span>
                <span className="text-xs tabular-nums text-muted">{rows.filter((p) => p.pod_id === pod.id).length} participantes</span>
              </li>
            ))}
          </ul>
        )}
        <form onSubmit={addPod} className="mt-4 flex gap-2">
          <input className="input" value={newPodName} onChange={(e) => setNewPodName(e.target.value)} placeholder="Nombre del pod" maxLength={200} aria-label="Nombre del nuevo pod" />
          <button type="submit" className="btn" disabled={!newPodName.trim()}>Añadir</button>
        </form>
        {podError && <p className="mt-2 text-sm text-danger">{podError}</p>}
      </section>
      <FormDrawer open={open} title={editing ? "Editar participante" : "Nuevo participante"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Nombre"><input className="input" value={form.full_name ?? ""} onChange={(e) => set("full_name", e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Cargo"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} maxLength={200} /></Field>
          <Field label="Área"><input className="input" value={form.area ?? ""} onChange={(e) => set("area", e.target.value)} maxLength={120} /></Field>
          <Field label="Pod">
            <select className="input" value={form.pod_id ?? ""} onChange={(e) => set("pod_id", e.target.value || null)}>
              <option value="">Sin pod</option>
              {podList.map((pod) => <option key={pod.id} value={pod.id}>{pod.name}</option>)}
            </select>
          </Field>
          <Field label="Estado"><Select value={form.is_active === false ? "Inactivo" : "Activo"} onChange={(v) => set("is_active", v === "Activo")} options={["Activo", "Inactivo"]} /></Field>
        </div>
      </FormDrawer>
    </div>
  );
}
