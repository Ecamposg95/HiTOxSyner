import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { actionsApi, ActionInput } from "../api/actions";
import { errorMessage } from "../api/client";
import { engagementsApi } from "../api/engagements";
import { initiativesApi } from "../api/initiatives";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { ACTION_STATUSES, LEVELS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Action } from "../types";

const EMPTY: ActionInput = { title: "", description: "", owner_name: "", owner_user_id: null, organization_side: "CLIENT", initiative_id: null, due_date: null, priority: "Medium", status: "Open", evidence: "" };

export function ActionsPage({ mine = false }: { mine?: boolean }) {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(
    () => actionsApi.list(engagementId, { status: status || undefined, mine: mine || undefined }),
    [engagementId, status, mine],
  );
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const writable = can(user, "write");
  const users = useResource(
    () => (writable ? engagementsApi.users(engagementId) : Promise.resolve([])),
    [engagementId, writable],
  );
  const [editing, setEditing] = useState<Action | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ActionInput>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function canEdit(a: Action) {
    return writable || (user?.role === "HITO_COLLABORATOR" && a.owner_user_id === user.id);
  }
  function openCreate() { setEditing(null); setForm(EMPTY); setFormError(null); setOpen(true); }
  function openEdit(a: Action) {
    if (!canEdit(a)) return;
    setEditing(a);
    setForm({ title: a.title, description: a.description, owner_name: a.owner_name, owner_user_id: a.owner_user_id, organization_side: a.organization_side, initiative_id: a.initiative_id, due_date: a.due_date, priority: a.priority, status: a.status, evidence: a.evidence });
    setFormError(null); setOpen(true);
  }
  const set = (key: keyof ActionInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));
  const limited = !!editing && !writable;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (editing) await actionsApi.update(editing.id, limited ? { status: form.status, evidence: form.evidence } : form);
      else await actionsApi.create(engagementId, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const initiativeName = (id: string | null) => initiatives.data?.items.find((i) => i.id === id)?.name ?? "—";

  return (
    <>
      <PageHeader
        title={mine ? "My Actions" : "Actions"}
        subtitle={mine ? "Compromisos asignados a ti" : "Registro de compromisos del engagement"}
        action={
          <div className="flex gap-2">
            <Link to={mine ? "/actions" : "/actions/mine"} className="btn">{mine ? "Ver todas" : "My Actions"}</Link>
            {writable && <button className="btn btn-primary" onClick={openCreate}>Nueva action</button>}
          </div>
        }
      />
      <div className="mb-4 w-48"><Select value={status} onChange={setStatus} options={ACTION_STATUSES} allowEmpty="Todos los estados" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Action>
          rows={data?.items ?? []}
          onRowClick={openEdit}
          empty={<EmptyState title={mine ? "No tienes acciones asignadas" : "Sin acciones"} />}
          columns={[
            { key: "title", header: "Action", render: (a) => <span className="font-medium">{a.title}<span className="block text-xs text-muted">{initiativeName(a.initiative_id)}</span></span> },
            { key: "owner", header: "Responsable", render: (a) => <span>{a.owner_name || "—"}<span className="block text-xs text-muted">{a.organization_side}</span></span> },
            { key: "due", header: "Fecha", render: (a) => formatDate(a.due_date), className: "tabular-nums" },
            { key: "priority", header: "Priority", render: (a) => <StatusBadge value={a.priority} /> },
            { key: "status", header: "Status", render: (a) => <StatusBadge value={a.status} /> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Actualizar action" : "Nueva action"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        {!limited && (
          <>
            <Field label="Acción"><input className="input" value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} required maxLength={200} /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Responsable (usuario)">
                <select className="input" value={form.owner_user_id ?? ""} onChange={(e) => set("owner_user_id", e.target.value || null)}>
                  <option value="">Sin usuario</option>
                  {users.data?.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
                </select>
              </Field>
              {!form.owner_user_id && (
                <Field label="Responsable (nombre)"><input className="input" value={form.owner_name ?? ""} onChange={(e) => set("owner_name", e.target.value)} maxLength={200} /></Field>
              )}
              <Field label="Organización"><Select value={form.organization_side ?? "CLIENT"} onChange={(v) => set("organization_side", v)} options={["CLIENT", "SYNER"]} /></Field>
              <Field label="Initiative">
                <select className="input" value={form.initiative_id ?? ""} onChange={(e) => set("initiative_id", e.target.value || null)}>
                  <option value="">Sin initiative</option>
                  {initiatives.data?.items.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
                </select>
              </Field>
              <Field label="Fecha compromiso"><input className="input" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value || null)} /></Field>
              <Field label="Priority"><Select value={form.priority ?? "Medium"} onChange={(v) => set("priority", v)} options={LEVELS} /></Field>
            </div>
            <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
          </>
        )}
        {limited && <p className="text-sm text-muted">{editing?.title}</p>}
        <Field label="Status"><Select value={form.status ?? "Open"} onChange={(v) => set("status", v)} options={ACTION_STATUSES} /></Field>
        <Field label="Evidencia"><textarea className="input" rows={3} value={form.evidence ?? ""} onChange={(e) => set("evidence", e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
