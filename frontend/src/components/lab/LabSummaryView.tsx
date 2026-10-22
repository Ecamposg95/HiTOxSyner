import { labApi } from "../../api/lab";
import { useResource } from "../../hooks/useResource";
import { formatDate } from "../../lib/dates";
import type { LabSummary } from "../../types";
import { Block } from "../Block";
import { EmptyState } from "../EmptyState";
import { KpiCard } from "../KpiCard";
import { PageHeader } from "../PageHeader";
import { StatusBadge } from "../StatusBadge";
import { CtaDonut, CtaStackedBars } from "./LabCharts";

export function LabSummaryContent({ data }: { data: LabSummary }) {
  if (data.sessions.length === 0) return <EmptyState title="El Lab aún no tiene sesiones programadas" />;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3">
        <KpiCard label="Sesiones realizadas" value={`${data.sessions_done}/${data.sessions.length}`} />
        <KpiCard label="Contratos activos" value={data.active_contracts} />
      </div>
      <Block title="CTAs por estado">
        <CtaDonut totals={data.cta_totals} evidencedPct={data.evidenced_pct} />
      </Block>
      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="CTAs por sesión">
          <CtaStackedBars rows={data.by_session.map((b) => ({ label: `${b.session_number}. ${b.session_name}`, totals: b.totals }))} />
        </Block>
        <Block title="CTAs por pod">
          <CtaStackedBars rows={data.by_pod.map((b) => ({ label: `${b.pod_number}. ${b.pod_name}`, totals: b.totals }))} />
        </Block>
      </div>
      <Block title="Sesiones">
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
      </Block>
    </div>
  );
}

export function LabSummaryView({ engagementId }: { engagementId: string }) {
  const { data, loading, error } = useResource(() => labApi.summary(engagementId), [engagementId]);
  return (
    <>
      <PageHeader eyebrow="Liderazgo" title="Executive Leadership Lab" subtitle="Avance agregado del programa de liderazgo" />
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : error || !data ? <p className="text-sm text-danger">{error}</p> : <LabSummaryContent data={data} />}
    </>
  );
}
