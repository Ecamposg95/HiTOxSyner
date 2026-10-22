import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { initiativesApi, InitiativeInput } from "../api/initiatives";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { EMPTY_INITIATIVE, InitiativeForm } from "../components/InitiativeForm";
import { PageHeader } from "../components/PageHeader";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { INITIATIVE_STATUSES } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Initiative } from "../types";

export function InitiativesPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useResource(() => initiativesApi.list(engagementId, { status: status || undefined }), [engagementId, status]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<InitiativeInput>(EMPTY_INITIATIVE);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      await initiativesApi.create(engagementId, form);
      setOpen(false); setForm(EMPTY_INITIATIVE);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader eyebrow="Estrategia" title="Initiatives" subtitle="Workstreams derivados del diagnóstico" action={can(user, "write") && <button className="btn btn-primary" onClick={() => setOpen(true)}>Nueva initiative</button>} />
      <div className="mb-4 w-48"><Select value={status} onChange={setStatus} options={INITIATIVE_STATUSES} allowEmpty="Todos los estados" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Initiative>
          rows={data?.items ?? []}
          onRowClick={(i) => navigate(`/initiatives/${i.id}`)}
          empty={<EmptyState title="Sin initiatives" hint="Las iniciativas se crean aquí o convirtiendo un finding." />}
          columns={[
            { key: "name", header: "Initiative", render: (i) => <span className="font-medium">{i.name}<span className="block text-xs text-muted">{i.hito_owner || "Sin owner HiTO"}</span></span> },
            { key: "status", header: "Status", render: (i) => <StatusBadge value={i.status} /> },
            { key: "priority", header: "Priority", render: (i) => <StatusBadge value={i.priority} /> },
            { key: "progress", header: "Progress", render: (i) => <div className="flex w-32 items-center gap-2"><ProgressBar value={i.progress_pct} /><span className="text-xs tabular-nums">{i.progress_pct}%</span></div> },
            { key: "target", header: "Target", render: (i) => formatDate(i.target_date), className: "tabular-nums" },
          ]}
        />
      )}
      <FormDrawer open={open} title="Nueva initiative" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <InitiativeForm form={form} onChange={setForm} />
      </FormDrawer>
    </>
  );
}
