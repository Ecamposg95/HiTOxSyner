import { Navigate, useSearchParams } from "react-router-dom";
import { ContractsTab } from "../components/lab/ContractsTab";
import { CtaTrackerTab } from "../components/lab/CtaTrackerTab";
import { LabSummaryContent, LabSummaryView } from "../components/lab/LabSummaryView";
import { ParticipantsTab } from "../components/lab/ParticipantsTab";
import { SessionsTab } from "../components/lab/SessionsTab";
import { PageHeader } from "../components/PageHeader";
import { labApi } from "../api/lab";
import { useResource } from "../hooks/useResource";
import { LAB_TABS, type LabTab } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

function SummaryTab({ engagementId }: { engagementId: string }) {
  const { data, loading, error } = useResource(() => labApi.summary(engagementId), [engagementId]);
  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <p className="text-sm text-danger">{error}</p>;
  return <LabSummaryContent data={data} />;
}

export function LabPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [params, setParams] = useSearchParams();
  if (!can(user, "viewLabSummary")) return <Navigate to="/" replace />;
  if (!can(user, "manageLab")) return <LabSummaryView engagementId={engagementId} />;
  const tab: LabTab = LAB_TABS.find((t) => t.key === params.get("tab"))?.key ?? "summary";
  return (
    <>
      <PageHeader eyebrow="Liderazgo" title="Executive Leadership Lab" subtitle="Sesiones, participantes, CTA tracker y Leadership Action Contracts" />
      <nav className="mb-5 flex flex-wrap gap-1 border-b border-line" aria-label="Secciones del Lab">
        {LAB_TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${tab === t.key ? "border-accent font-medium text-ink" : "border-transparent text-muted hover:text-ink"}`}
            aria-current={tab === t.key ? "page" : undefined}
            onClick={() => setParams({ tab: t.key })}
          >
            {t.label}
          </button>
        ))}
      </nav>
      {tab === "summary" && <SummaryTab engagementId={engagementId} />}
      {tab === "sessions" && <SessionsTab engagementId={engagementId} />}
      {tab === "participants" && <ParticipantsTab engagementId={engagementId} />}
      {tab === "ctas" && <CtaTrackerTab engagementId={engagementId} />}
      {tab === "contracts" && <ContractsTab engagementId={engagementId} />}
    </>
  );
}
