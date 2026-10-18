import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { initiativesApi } from "../api/initiatives";
import { milestonesApi, MilestoneInput } from "../api/milestones";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { MILESTONE_STATUSES, ROADMAP_PHASES } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Milestone, RoadmapPhase } from "../types";

const EMPTY: MilestoneInput = { name: "", description: "", phase: "Discover", due_date: null, status: "Planned", owner: "", initiative_id: null, deliverable: "" };

export function RoadmapPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => milestonesApi.list(engagementId), [engagementId]);
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const writable = can(user, "write");
  const [editing, setEditing] = useState<Milestone | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<MilestoneInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreate(phase: RoadmapPhase = "Discover") { setEditing(null); setForm({ ...EMPTY, phase }); setFormError(null); setOpen(true); }
  function openEdit(m: Milestone) {
    if (!writable) return;
    setEditing(m);
    setForm({ name: m.name, description: m.description, phase: m.phase, due_date: m.due_date, status: m.status, owner: m.owner, initiative_id: m.initiative_id, deliverable: m.deliverable });
    setFormError(null); setOpen(true);
  }
  const set = (key: keyof MilestoneInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await milestonesApi.update(editing.id, form);
      else await milestonesApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const items = data?.items ?? [];
  const initiativeName = (id: string | null) => initiatives.data?.items.find((i) => i.id === id)?.name;

  return (
    <>
      <PageHeader title="Transformation Roadmap" subtitle="Seis fases del programa y sus milestones" action={writable && <button className="btn btn-primary" onClick={() => openCreate()}>Nuevo milestone</button>} />
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : items.length === 0 ? (
        <EmptyState title="Sin milestones" hint={writable ? "Crea el primer milestone del roadmap." : undefined} />
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          {ROADMAP_PHASES.map((phase) => {
            const inPhase = items.filter((m) => m.phase === phase);
            const done = inPhase.filter((m) => m.status === "Done").length;
            return (
              <section key={phase} className="card flex flex-col p-3">
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-sm font-semibold">{phase}</h2>
                  <span className="text-xs tabular-nums text-muted">{done}/{inPhase.length}</span>
                </div>
                <ul className="flex-1 space-y-2">
                  {inPhase.map((m) => (
                    <li
                      key={m.id}
                      onClick={() => openEdit(m)}
                      onKeyDown={writable ? (e) => { if (e.target !== e.currentTarget) return; if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openEdit(m); } } : undefined}
                      tabIndex={writable ? 0 : undefined}
                      role={writable ? "button" : undefined}
                      className={`rounded border border-line p-2 text-sm ${writable ? "cursor-pointer hover:bg-canvas focus:bg-canvas focus:outline-none" : ""}`}
                    >
                      <div className="font-medium leading-5">{m.name}</div>
                      <div className="mt-1 flex items-center justify-between gap-2">
                        <span className="text-xs tabular-nums text-muted">{formatDate(m.due_date)}</span>
                        <StatusBadge value={m.status} />
                      </div>
                      {m.initiative_id && <div className="mt-1 truncate text-xs text-muted">{initiativeName(m.initiative_id)}</div>}
                    </li>
                  ))}
                </ul>
                {writable && <button className="btn mt-3 w-full justify-center text-xs" onClick={() => openCreate(phase)}>+ Milestone</button>}
              </section>
            );
          })}
        </div>
      )}
      <FormDrawer open={open} title={editing ? "Editar milestone" : "Nuevo milestone"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Nombre"><input className="input" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Phase"><Select value={form.phase ?? "Discover"} onChange={(v) => set("phase", v)} options={ROADMAP_PHASES} /></Field>
          <Field label="Status"><Select value={form.status ?? "Planned"} onChange={(v) => set("status", v)} options={MILESTONE_STATUSES} /></Field>
          <Field label="Fecha objetivo"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
          <Field label="Owner"><input className="input" value={form.owner ?? ""} onChange={(e) => set("owner", e.target.value)} maxLength={200} /></Field>
          <Field label="Initiative">
            <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
              <option value="">Sin initiative</option>
              {initiatives.data?.items.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Deliverable"><textarea className="input" rows={2} value={form.deliverable ?? ""} onChange={(e) => set("deliverable", e.target.value)} /></Field>
        <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
