import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { documentsApi } from "../api/documents";
import { initiativesApi, InitiativeInput } from "../api/initiatives";
import { Block, Prose } from "../components/Block";
import { Comments } from "../components/Comments";
import { EmptyState } from "../components/EmptyState";
import { FormDrawer } from "../components/FormDrawer";
import { InitiativeForm, initiativeToInput } from "../components/InitiativeForm";
import { KpiCard } from "../components/KpiCard";
import { PageHeader } from "../components/PageHeader";
import { ProgressRing } from "../components/ProgressRing";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

export function InitiativeDetailPage() {
  const { id = "" } = useParams();
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => initiativesApi.detail(id), [id]);
  const writable = can(user, "write");
  const allDocuments = useResource(() => (writable ? documentsApi.list(engagementId) : Promise.resolve(null)), [engagementId, writable]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<InitiativeInput>({});
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [linkId, setLinkId] = useState("");
  const [linkError, setLinkError] = useState<string | null>(null);

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

  async function link() {
    if (!linkId) return;
    setLinkError(null);
    try {
      await documentsApi.addLink(linkId, { entity_type: "initiative", entity_id: id });
      setLinkId("");
      await Promise.all([reload(), allDocuments.reload()]);
    } catch (err) { setLinkError(errorMessage(err)); }
  }

  async function unlink(documentId: string) {
    const doc = data?.documents.find((d) => d.id === documentId);
    const docLink = doc?.links.find((l) => l.entity_type === "initiative" && l.entity_id === id);
    if (!docLink) return;
    setLinkError(null);
    try {
      await documentsApi.removeLink(documentId, docLink.id);
      await Promise.all([reload(), allDocuments.reload()]);
    } catch (err) { setLinkError(errorMessage(err)); }
  }

  const linkedIds = new Set(data.documents.map((d) => d.id));
  const linkable = allDocuments.data?.items.filter((d) => !linkedIds.has(d.id)) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <Link to="/initiatives" className="mb-3 inline-block text-xs text-muted hover:underline">← Initiatives</Link>
        <PageHeader
          eyebrow={i.area || "Initiative"}
          title={i.name}
          action={writable ? <button className="btn" onClick={() => { setForm(initiativeToInput(i)); setFormError(null); setOpen(true); }}>Editar</button> : undefined}
        />
        <div className="-mt-3 flex flex-wrap items-center gap-2">
          <StatusBadge value={i.status} />
          <StatusBadge value={i.priority} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Avance" value={`${i.progress_pct}%`} visual={<ProgressRing value={i.progress_pct} size={44} />} />
        <KpiCard label="Owner HiTO" value={<span className="font-display text-lg break-words">{i.hito_owner || "—"}</span>} />
        <KpiCard label="Inicio" value={<span className="font-display text-lg">{formatDate(i.start_date)}</span>} />
        <KpiCard label="Objetivo" value={<span className="font-display text-lg">{formatDate(i.target_date)}</span>} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div className="min-w-0 space-y-6">
          <Block title="Objetivo"><Prose text={i.objective} /></Block>
          <Block title="Descripción"><Prose text={i.description} /></Block>
          <Block title="Resultado esperado"><Prose text={i.expected_outcome} /></Block>
          <Block title="Risks"><Prose text={i.risks} /></Block>
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
        <div className="min-w-0 space-y-6">
        <Block title="Milestones" action={<Link to="/roadmap" className="text-xs text-muted hover:underline">Roadmap →</Link>}>
          {data.milestones.length === 0 ? <p className="text-sm text-muted">Sin milestones vinculados.</p> : (
            <ul className="space-y-2">
              {data.milestones.map((m) => (
                <li key={m.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{m.name}<span className="block text-xs text-muted">{m.phase} · {formatDate(m.due_date)}</span></span>
                  <StatusBadge value={m.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Actions" action={<Link to="/actions" className="text-xs text-muted hover:underline">Actions →</Link>}>
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
        <Block title="Decisions" action={<Link to="/decisions" className="text-xs text-muted hover:underline">Decision Log →</Link>}>
          {data.decisions.length === 0 ? <p className="text-sm text-muted">Sin decisiones vinculadas.</p> : (
            <ul className="space-y-2">
              {data.decisions.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{d.title}<span className="block text-xs text-muted">{d.owner_name || "Sin owner"} · {formatDate(d.decided_on)}</span></span>
                  <StatusBadge value={d.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Findings origen">
          {data.findings.length === 0 ? <p className="text-sm text-muted">Esta iniciativa no proviene de un finding.</p> : (
            <ul className="space-y-2">
              {data.findings.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-3 text-sm"><span>{f.title}</span><StatusBadge value={f.impact} /></li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Documents">
          {data.documents.length === 0 ? <p className="text-sm text-muted">Sin documentos vinculados.</p> : (
            <ul className="space-y-2">
              {data.documents.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>
                    {d.url ? <a href={d.url} target="_blank" rel="noreferrer" className="hover:underline">{d.name}</a> : d.name}
                    <span className="block text-xs text-muted">{d.category}{d.version ? ` · v${d.version}` : ""}{d.internal_only ? " · Interno" : ""}</span>
                  </span>
                  {writable && <button className="btn text-xs" onClick={() => unlink(d.id)}>Quitar</button>}
                </li>
              ))}
            </ul>
          )}
          {writable && (
            <div className="mt-3 flex gap-2">
              <select className="input" value={linkId} onChange={(e) => setLinkId(e.target.value)}>
                <option value="">Vincular documento…</option>
                {linkable.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              <button className="btn" onClick={link} disabled={!linkId}>Vincular</button>
            </div>
          )}
          {linkError && <p className="mt-2 text-sm text-danger">{linkError}</p>}
        </Block>
        <Comments entityType="initiative" entityId={id} />
        </div>
      </div>

      <FormDrawer open={open} title="Editar initiative" onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <InitiativeForm form={form} onChange={setForm} />
      </FormDrawer>
    </div>
  );
}
