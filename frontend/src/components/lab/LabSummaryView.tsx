import { labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import type { CtaStatusTotals } from "../../types";
import { EmptyState } from "../EmptyState";
import { PageHeader } from "../PageHeader";
import { StatusBadge } from "../StatusBadge";
import { Tile } from "../Tile";

const SEGMENTS: { key: keyof Omit<CtaStatusTotals, "total">; label: string; className: string }[] = [
  { key: "evidenced", label: "Evidenced", className: "bg-accent" },
  { key: "in_progress", label: "In Progress", className: "bg-warn" },
  { key: "committed", label: "Committed", className: "bg-gray-400" },
  { key: "dropped", label: "Dropped", className: "bg-gray-200" },
];

export function CtaStatusBar({ totals }: { totals: CtaStatusTotals }) {
  if (totals.total === 0) return <div className="h-2 w-full rounded bg-line" role="img" aria-label="Sin CTAs" />;
  return (
    <div className="flex h-2 w-full overflow-hidden rounded bg-line" role="img" aria-label={SEGMENTS.map((s) => `${s.label}: ${totals[s.key]}`).join(", ")}>
      {SEGMENTS.filter((s) => totals[s.key] > 0).map((s) => (
        <div key={s.key} className={s.className} style={{ width: `${(100 * totals[s.key]) / totals.total}%` }} title={`${s.label}: ${totals[s.key]}`} />
      ))}
    </div>
  );
}

export function CtaLegend() {
  return (
    <p className="flex flex-wrap gap-4 text-xs text-muted">
      {SEGMENTS.map((s) => (
        <span key={s.key} className="flex items-center gap-1"><span className={`inline-block h-2 w-2 rounded ${s.className}`} />{s.label}</span>
      ))}
    </p>
  );
}

function Breakdown({ title, rows }: { title: string; rows: { key: number; label: string; totals: CtaStatusTotals }[] }) {
  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
      {rows.length === 0 ? <p className="text-sm text-muted">Sin datos.</p> : (
        <ul className="space-y-3">
          {rows.map((r) => (
            <li key={r.key} className="text-sm">
              <div className="mb-1 flex items-center justify-between gap-3">
                <span>{r.label}</span>
                <span className="text-xs tabular-nums text-muted">{r.totals.evidenced}/{r.totals.total} con evidencia</span>
              </div>
              <CtaStatusBar totals={r.totals} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function LabSummaryView({ engagementId }: { engagementId: string }) {
  const { data, loading, error } = useResource(() => labApi.summary(engagementId), [engagementId]);
  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <p className="text-sm text-danger">{error}</p>;
  const activeCtas = data.cta_totals.committed + data.cta_totals.in_progress;
  return (
    <>
      <PageHeader title="Executive Leadership Lab" subtitle="Avance agregado del programa de liderazgo" />
      {data.sessions.length === 0 ? <EmptyState title="El Lab aún no tiene sesiones programadas" /> : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Tile label="Sesiones realizadas" value={`${data.sessions_done}/${data.sessions.length}`} />
            <Tile label="CTAs activos" value={activeCtas} />
            <Tile label="CTAs con evidencia" value={`${data.evidenced_pct}%`} tone={data.evidenced_pct >= 50 ? "ok" : "default"} />
            <Tile label="Contratos activos" value={data.active_contracts} />
          </div>
          <section className="card p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">Sesiones</h2>
            <ul className="divide-y divide-line">
              {data.sessions.map((s) => (
                <li key={s.number} className="flex flex-wrap items-center justify-between gap-3 py-2 text-sm">
                  <span className="font-medium">{s.number}. {s.name}<span className="block text-xs font-normal text-muted">{s.theme}</span></span>
                  <span className="flex items-center gap-3 text-xs tabular-nums text-muted">
                    <span>{formatDate(s.held_on)}</span>
                    <span>{s.attendance_count !== null ? `${s.attendance_count} asistentes` : "—"}</span>
                    <StatusBadge value={s.status} />
                  </span>
                </li>
              ))}
            </ul>
          </section>
          <div className="grid gap-6 lg:grid-cols-2">
            <Breakdown title="CTAs por sesión" rows={data.by_session.map((b) => ({ key: b.session_number, label: `${b.session_number}. ${b.session_name}`, totals: b.totals }))} />
            <Breakdown title="CTAs por pod" rows={data.by_pod.map((b) => ({ key: b.pod_number, label: `${b.pod_number}. ${b.pod_name}`, totals: b.totals }))} />
          </div>
          <CtaLegend />
        </div>
      )}
    </>
  );
}
