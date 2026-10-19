import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ActionInput } from "../api/actions";
import { errorMessage } from "../api/client";
import { DecisionInput } from "../api/decisions";
import { engagementsApi } from "../api/engagements";
import { initiativesApi } from "../api/initiatives";
import { meetingsApi, MeetingInput } from "../api/meetings";
import { ActionForm, EMPTY_ACTION } from "../components/ActionForm";
import { Block, Prose } from "../components/Block";
import { Comments } from "../components/Comments";
import { DecisionForm, EMPTY_DECISION } from "../components/DecisionForm";
import { EmptyState } from "../components/EmptyState";
import { FormDrawer } from "../components/FormDrawer";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate, formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import { MeetingForm } from "./MeetingsPage";

type Drawer = "none" | "edit" | "decision" | "action";

export function MeetingDetailPage() {
  const { id = "" } = useParams();
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => meetingsApi.detail(id), [id]);
  const writable = can(user, "write");
  const initiatives = useResource(() => initiativesApi.list(engagementId), [engagementId]);
  const users = useResource(() => (writable ? engagementsApi.users(engagementId) : Promise.resolve([])), [engagementId, writable]);
  const [drawer, setDrawer] = useState<Drawer>("none");
  const [meetingForm, setMeetingForm] = useState<MeetingInput>({});
  const [decisionForm, setDecisionForm] = useState<DecisionInput>(EMPTY_DECISION);
  const [actionForm, setActionForm] = useState<ActionInput>(EMPTY_ACTION);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (loading && !data) return <p className="text-sm text-muted">Cargando…</p>;
  if (error || !data) return <EmptyState title="Meeting no encontrada" hint={error ?? undefined} />;
  const m = data.meeting;

  function openDrawer(kind: Drawer) {
    if (kind === "edit") setMeetingForm({ title: m.title, held_on: m.held_on, participants: m.participants, objective: m.objective, summary: m.summary, discussion: m.discussion, next_steps: m.next_steps });
    if (kind === "decision") setDecisionForm(EMPTY_DECISION);
    if (kind === "action") setActionForm(EMPTY_ACTION);
    setFormError(null); setDrawer(kind);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    try {
      if (drawer === "edit") await meetingsApi.update(id, meetingForm);
      if (drawer === "decision") await meetingsApi.createDecision(id, decisionForm);
      if (drawer === "action") await meetingsApi.createAction(id, actionForm);
      setDrawer("none");
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  const titles: Record<Drawer, string> = { none: "", edit: "Editar meeting", decision: "Registrar decisión", action: "Registrar acción" };

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link to="/meetings" className="text-xs text-muted hover:underline">← Meetings</Link>
            <h1 className="mt-1 text-xl font-semibold tracking-tight">{m.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted">
              <span className="tabular-nums">{formatDateTime(m.held_on)}</span>
              <span>Participantes: {m.participants || "—"}</span>
            </div>
          </div>
          {writable && <button className="btn" onClick={() => openDrawer("edit")}>Editar</button>}
        </div>
        {m.objective && <p className="mt-4 text-sm leading-6"><span className="font-medium">Objetivo: </span>{m.objective}</p>}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Block title="Summary"><Prose text={m.summary} /></Block>
        <Block title="Discussion"><Prose text={m.discussion} /></Block>
        <Block title="Decisions" action={writable && <button className="btn" onClick={() => openDrawer("decision")}>Registrar decisión</button>}>
          {data.decisions.length === 0 ? <p className="text-sm text-muted">Sin decisiones registradas en esta reunión.</p> : (
            <ul className="space-y-2">
              {data.decisions.map((d) => (
                <li key={d.id} className="flex items-start justify-between gap-3 text-sm">
                  <Link to="/decisions" className="hover:underline">{d.title}<span className="block text-xs text-muted">{d.owner_name || "Sin owner"}</span></Link>
                  <StatusBadge value={d.status} />
                </li>
              ))}
            </ul>
          )}
        </Block>
        <Block title="Action Items" action={writable && <button className="btn" onClick={() => openDrawer("action")}>Registrar acción</button>}>
          {data.actions.length === 0 ? <p className="text-sm text-muted">Sin acciones derivadas.</p> : (
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
        <Block title="Next Steps"><Prose text={m.next_steps} /></Block>
        <Comments entityType="meeting" entityId={id} />
      </div>

      <FormDrawer open={drawer !== "none"} title={titles[drawer]} onClose={() => setDrawer("none")} onSubmit={submit} submitting={busy} error={formError}>
        {drawer === "edit" && <MeetingForm form={meetingForm} onChange={setMeetingForm} />}
        {drawer === "decision" && <DecisionForm form={decisionForm} onChange={setDecisionForm} initiatives={initiatives.data?.items ?? []} />}
        {drawer === "action" && <ActionForm form={actionForm} onChange={setActionForm} users={users.data ?? []} initiatives={initiatives.data?.items ?? []} />}
      </FormDrawer>
    </div>
  );
}
