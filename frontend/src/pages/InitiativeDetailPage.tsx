import { FormEvent, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { initiativesApi, InitiativeInput } from "../api/initiatives";
import { EmptyState } from "../components/EmptyState";
import { FormDrawer } from "../components/FormDrawer";
import { InitiativeForm, initiativeToInput } from "../components/InitiativeForm";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
      {children}
    </section>
  );
}

function Prose({ text }: { text: string }) {
  return <p className="whitespace-pre-line text-sm leading-6">{text || <span className="text-muted">Sin contenido.</span>}</p>;
}

export function InitiativeDetailPage() {
  const { id = "" } = useParams();
  const user = useAuthStore((s) => s.user);
  const { data, loading, error, reload } = useResource(() => initiativesApi.detail(id), [id]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<InitiativeInput>({});
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <EmptyState title="Initiative no encontrada" hint={error ?? undefined} />;
  const i = data.initiative;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      await initiativesApi.update(id, form);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link to="/initiatives" className="text-xs text-muted hover:underline">← Initiatives</Link>
            <h1 className="mt-1 text-xl font-semibold tracking-tight">{i.name}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted">
              <StatusBadge value={i.status} />
              <StatusBadge value={i.priority} />
              <span>Owner HiTO: {i.hito_owner || "—"}</span>
              <span>Target: {formatDate(i.target_date)}</span>
            </div>
          </div>
          {can(user, "write") && <button className="btn" onClick={() => { setForm(initiativeToInput(i)); setFormError(null); setOpen(true); }}>Editar</button>}
        </div>
        <div className="mt-4 flex items-center gap-3">
          <ProgressBar value={i.progress_pct} />
          <span className="text-sm tabular-nums">{i.progress_pct}%</span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Objective"><Prose text={i.objective} /></Block>
        <Block title="Expected Outcome"><Prose text={i.expected_outcome} /></Block>
        <Block title="Milestones"><p className="text-sm text-muted">Disponible en la siguiente entrega.</p></Block>
        <Block title="Actions">
          {data.actions.length === 0 ? <p className="text-sm text-muted">Sin acciones vinculadas.</p> : (
            <ul className="space-y-2">
              {data.actions.map((a) => (
                <li key={a.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{a.title}<span className="block text-xs text-muted">{a.owner_name || "Sin responsable"} · {formatDate(a.due_date)}</span></span>
                  <StatusBadge value={a.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Decisions"><p className="text-sm text-muted">Disponible en la siguiente entrega.</p></Block>
        <Block title="Risks"><Prose text={i.risks} /></Block>
        <Block title="Findings origen">
          {data.findings.length === 0 ? <p className="text-sm text-muted">Esta iniciativa no proviene de un finding.</p> : (
            <ul className="space-y-2">
              {data.findings.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-3 text-sm"><span>{f.title}</span><StatusBadge value={f.impact} /></li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Documents"><p className="text-sm text-muted">Disponible en la siguiente entrega.</p></Block>
        <Block title="Activity">
          {data.activity.length === 0 ? <p className="text-sm text-muted">Sin actividad.</p> : (
            <ul className="space-y-2">
              {data.activity.map((a) => (
                <li key={a.id} className="text-sm">{a.summary}<span className="block text-xs text-muted">{formatDateTime(a.created_at)}</span></li>
              ))}
            </ul>
          )}
        </Block>
      </div>

      <FormDrawer open={open} title="Editar initiative" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <InitiativeForm form={form} onChange={setForm} />
      </FormDrawer>
    </div>
  );
}
