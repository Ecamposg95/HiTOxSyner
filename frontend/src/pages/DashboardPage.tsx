import { useState } from "react";
import { Link } from "react-router-dom";
import { engagementsApi } from "../api/engagements";
import { errorMessage } from "../api/client";
import { Block } from "../components/Block";
import { EmptyState } from "../components/EmptyState";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { KpiCard } from "../components/KpiCard";
import { PageHeader } from "../components/PageHeader";
import { ProgressRing } from "../components/ProgressRing";
import { avgProgress, initiativeTone, isOverdue, phaseProgress, todayLocal } from "../lib/cockpit";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

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

  const { tiles, engagement } = data;
  const today = todayLocal();
  const avg = avgProgress(data.active_initiatives);
  const DOT = { accent: "bg-accent", muted: "bg-muted", warn: "bg-warn" } as const;
  const more = (to: string, label: string) => <Link to={to} className="text-xs text-muted hover:underline">{label}</Link>;

  const nextMilestones = (
    <Block title="Próximos hitos">
      {data.next_milestones.length === 0 ? <p className="text-sm text-muted">Sin milestones programados.</p> : (
        <ul className="space-y-2">
          {data.next_milestones.map((m) => (
            <li key={m.id} className="flex items-start justify-between gap-3 text-sm">
              <span className="min-w-0">{m.name}<span className="block text-xs text-muted">{m.phase}</span></span>
              <span className="flex shrink-0 items-center gap-2 text-xs tabular-nums text-muted">{formatDate(m.due_date)}<StatusBadge value={m.status} /></span>
            </li>
          ))}
        </ul>
      )}
    </Block>
  );

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
      <PageHeader eyebrow="Syner × HiTO · Engagement" title={engagement.name} subtitle={engagement.subtitle ?? undefined} />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Avance del programa" value={`${tiles.progress_pct}%`} visual={<ProgressRing value={tiles.progress_pct} />} note={<StatusBadge value={tiles.health} />} />
        <KpiCard label="Initiatives activas" value={tiles.active_initiatives} note={`avance promedio ${avg ?? "—"}% · ${tiles.open_actions} acciones abiertas`} />
        <KpiCard label="Decisiones pendientes" value={tiles.decisions_required} tone={tiles.decisions_required > 0 ? "warn" : "default"} note="requieren a Dirección" />
        <KpiCard label="Findings críticos" value={tiles.critical_findings} tone={tiles.critical_findings > 0 ? "danger" : "default"} />
      </div>

      <Block title="Resumen ejecutivo">
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
            <p className="whitespace-pre-line font-display text-[15px] leading-7">{engagement.executive_summary || "Sin resumen ejecutivo todavía."}</p>
            {can(user, "write") && (
              <button className="btn" onClick={() => { setSummary(engagement.executive_summary); setEditing(true); }}>Editar</button>
            )}
          </div>
        )}
      </Block>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Roadmap por fase" action={more("/roadmap", "Roadmap →")}>
          <ul className="space-y-3">
            {data.roadmap.map((phase) => {
              const pct = phaseProgress(phase.milestones);
              return (
                <li key={phase.phase} className="flex items-center gap-3 text-sm">
                  <Link to="/roadmap" className="w-24 shrink-0 font-medium hover:underline">{phase.phase}</Link>
                  <ProgressBar value={pct ?? 0} />
                  <span className="w-10 shrink-0 text-right text-xs tabular-nums text-muted">{pct === null ? "—" : `${pct}%`}</span>
                </li>
              );
            })}
          </ul>
        </Block>

        <Block title="Decisiones requeridas" action={more("/decisions", "Decision Log →")}>
          {data.decisions_required.length === 0 ? (
            <p className="text-sm text-muted">Sin decisiones pendientes de aprobación.</p>
          ) : (
            <ul className="space-y-2">
              {data.decisions_required.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <Link to="/decisions" className="min-w-0 hover:underline">{d.title}<span className="block text-xs text-muted">{d.owner_name || "Sin owner"}</span></Link>
                  {d.decided_on ? (
                    <span className="flex shrink-0 items-center gap-2 text-xs tabular-nums text-muted">
                      {formatDate(d.decided_on)}
                      {isOverdue(d.decided_on, today) && <span className="badge badge-danger">Vencida</span>}
                    </span>
                  ) : (
                    <StatusBadge value={d.status} />
                  )}
                </li>
              ))}
            </ul>
          )}
        </Block>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Block title="Initiatives" action={more("/initiatives", "Initiatives →")}>
          {data.active_initiatives.length === 0 ? (
            <p className="text-sm text-muted">Sin iniciativas activas.</p>
          ) : (
            <ul className="space-y-2">
              {data.active_initiatives.map((i) => (
                <li key={i.id} className="flex items-center gap-2 text-sm">
                  <span className={`h-2 w-2 shrink-0 rounded-full ${DOT[initiativeTone(i.status)]}`} aria-hidden="true" />
                  <Link to={`/initiatives/${i.id}`} className="min-w-0 flex-1 truncate hover:underline" title={i.name}>{i.name}</Link>
                  <span className="text-xs tabular-nums text-muted">{i.progress_pct}%</span>
                </li>
              ))}
            </ul>
          )}
        </Block>

        {nextMilestones}

        {data.lab ? (
          <Block title="Leadership Lab" action={more("/lab", "Leadership Lab →")}>
            <div className="space-y-4 text-sm">
              <div>
                <div className="eyebrow">Próxima sesión</div>
                {data.lab.next_session ? (
                  <>
                    <div className="mt-1 font-medium">{data.lab.next_session.number}. {data.lab.next_session.name}</div>
                    <div className="text-xs tabular-nums text-muted">{data.lab.next_session.theme} · {formatDate(data.lab.next_session.held_on)}</div>
                  </>
                ) : (
                  <div className="mt-1 text-muted">Sin sesiones pendientes</div>
                )}
              </div>
              <div>
                <div className="eyebrow">CTAs con evidencia</div>
                <div className="mt-1 flex items-center gap-3">
                  <ProgressBar value={data.lab.evidenced_pct} />
                  <span className="text-xs tabular-nums text-muted">{data.lab.evidenced_pct}%</span>
                </div>
                <div className="mt-1 text-xs text-muted">{data.lab.active_contracts} contratos activos</div>
              </div>
            </div>
          </Block>
        ) : (
          <Block title="Próximas acciones" action={more("/actions", "Actions →")}>
            {data.next_actions.length === 0 ? (
              <p className="text-sm text-muted">Sin acciones abiertas.</p>
            ) : (
              <ul className="space-y-2">
                {data.next_actions.map((a) => (
                  <li key={a.id} className="flex items-start justify-between gap-3 text-sm">
                    <span className="min-w-0">{a.title}<span className="block text-xs text-muted">{a.owner_name || "Sin responsable"}</span></span>
                    <span className="shrink-0 text-xs tabular-nums text-muted">{formatDate(a.due_date)}</span>
                  </li>
                ))}
              </ul>
            )}
          </Block>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Key findings">
          {data.key_findings.length === 0 ? (
            <p className="text-sm text-muted">Sin hallazgos de alto impacto.</p>
          ) : (
            <ul className="space-y-2">
              {data.key_findings.map((f) => (
                <li key={f.id} className="flex items-start justify-between gap-3 text-sm">
                  <span className="min-w-0">{f.title}</span>
                  <StatusBadge value={f.impact} />
                </li>
              ))}
            </ul>
          )}
        </Block>

        <Block title="Actividad reciente">
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
        </Block>
      </div>
    </div>
  );
}
