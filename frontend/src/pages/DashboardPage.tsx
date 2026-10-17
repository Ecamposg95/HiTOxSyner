import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { engagementsApi } from "../api/engagements";
import { errorMessage } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { Tile } from "../components/Tile";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
      {children}
    </section>
  );
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { current, refreshCurrent } = useEngagementStore();
  const engagementId = current?.id ?? "";
  const { data, loading, error, reload } = useResource(() => engagementsApi.dashboard(engagementId), [engagementId]);
  const [editing, setEditing] = useState(false);
  const [summary, setSummary] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  if (!current) return <EmptyState title="Sin engagement asignado" />;
  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <p className="text-sm text-danger">{error}</p>;

  const healthTone = data.tiles.health === "On Track" ? "ok" : data.tiles.health === "Attention" ? "warn" : "danger";

  async function saveSummary() {
    try {
      await engagementsApi.update(engagementId, { executive_summary: summary });
      setEditing(false);
      await Promise.all([reload(), refreshCurrent()]);
    } catch (err) {
      setSaveError(errorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs font-semibold tracking-[0.3em]">SYNER × HiTO</div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{data.engagement.name}</h1>
        {data.engagement.subtitle && <p className="text-sm text-muted">{data.engagement.subtitle}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Tile label="Engagement Health" value={data.tiles.health} tone={healthTone} />
        <Tile label="Progress" value={`${data.tiles.progress_pct}%`} />
        <Tile label="Active Initiatives" value={data.tiles.active_initiatives} />
        <Tile label="Open Actions" value={data.tiles.open_actions} />
        <Tile label="Decisions Required" value={data.tiles.decisions_required} tone={data.tiles.decisions_required > 0 ? "warn" : "default"} />
        <Tile label="Critical Findings" value={data.tiles.critical_findings} tone={data.tiles.critical_findings > 0 ? "danger" : "default"} />
      </div>

      <Section title="Executive Summary">
        {editing ? (
          <div className="space-y-2">
            <textarea className="input min-h-[120px]" value={summary} onChange={(e) => setSummary(e.target.value)} maxLength={2000} />
            {saveError && <p className="text-sm text-danger">{saveError}</p>}
            <div className="flex gap-2">
              <button className="btn btn-primary" onClick={saveSummary}>Guardar</button>
              <button className="btn" onClick={() => setEditing(false)}>Cancelar</button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-4">
            <p className="whitespace-pre-line text-sm leading-6">{data.engagement.executive_summary || "Sin resumen ejecutivo todavía."}</p>
            {can(user, "write") && (
              <button className="btn" onClick={() => { setSummary(data.engagement.executive_summary); setEditing(true); }}>Editar</button>
            )}
          </div>
        )}
      </Section>

      <Section title="Transformation Roadmap">
        <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
          {data.roadmap.map((phase) => {
            const done = phase.milestones.filter((m) => m.status === "Done").length;
            return (
              <Link key={phase.phase} to="/roadmap" className="rounded border border-line px-3 py-2 hover:bg-canvas">
                <div className="text-sm font-medium">{phase.phase}</div>
                <div className="text-xs tabular-nums text-muted">{done}/{phase.milestones.length} milestones</div>
                <ul className="mt-1 space-y-0.5">
                  {phase.milestones.slice(0, 3).map((m) => (
                    <li key={m.id} className="truncate text-xs" title={m.name}>{m.name}</li>
                  ))}
                </ul>
              </Link>
            );
          })}
        </div>
      </Section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Active Initiatives">
          {data.active_initiatives.length === 0 ? (
            <p className="text-sm text-muted">Sin iniciativas activas.</p>
          ) : (
            <ul className="space-y-3">
              {data.active_initiatives.map((i) => (
                <li key={i.id}>
                  <div className="flex items-center justify-between gap-3">
                    <Link to={`/initiatives/${i.id}`} className="text-sm font-medium hover:underline">{i.name}</Link>
                    <StatusBadge value={i.status} />
                  </div>
                  <div className="mt-1 flex items-center gap-3">
                    <ProgressBar value={i.progress_pct} />
                    <span className="text-xs tabular-nums text-muted">{i.progress_pct}%</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Decisions Required">
          {data.decisions_required.length === 0 ? (
            <p className="text-sm text-muted">Sin decisiones pendientes de aprobación.</p>
          ) : null}
        </Section>

        <Section title="Key Findings">
          {data.key_findings.length === 0 ? (
            <p className="text-sm text-muted">Sin hallazgos de alto impacto.</p>
          ) : (
            <ul className="space-y-2">
              {data.key_findings.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{f.title}</span>
                  <StatusBadge value={f.impact} />
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Next">
          {data.next_actions.length === 0 ? (
            <p className="text-sm text-muted">Sin acciones abiertas.</p>
          ) : (
            <ul className="space-y-2">
              {data.next_actions.map((a) => (
                <li key={a.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{a.title}<span className="block text-xs text-muted">{a.owner_name || "Sin responsable"}</span></span>
                  <span className="text-xs tabular-nums text-muted">{formatDate(a.due_date)}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Recent Activity">
          {data.recent_activity.length === 0 ? (
            <p className="text-sm text-muted">Sin actividad.</p>
          ) : (
            <ul className="space-y-2">
              {data.recent_activity.map((a) => (
                <li key={a.id} className="text-sm">
                  {a.summary}
                  <span className="block text-xs text-muted">{formatDateTime(a.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Next Milestones">
          {data.next_milestones.length === 0 ? <p className="text-sm text-muted">Sin milestones programados.</p> : (
            <ul className="space-y-2">
              {data.next_milestones.map((m) => (
                <li key={m.id} className="flex items-start justify-between gap-3 text-sm">
                  <span>{m.name}<span className="block text-xs text-muted">{m.phase}</span></span>
                  <span className="flex items-center gap-2 text-xs tabular-nums text-muted">{formatDate(m.due_date)}<StatusBadge value={m.status} /></span>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>
    </div>
  );
}
