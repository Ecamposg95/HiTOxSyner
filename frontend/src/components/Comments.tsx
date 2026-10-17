import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { commentsApi } from "../api/comments";
import { useResource } from "../hooks/useResource";
import { formatDateTime } from "../lib/dates";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

export function Comments({ entityType, entityId }: { entityType: string; entityId: string }) {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const { data, loading, error, reload } = useResource(() => commentsApi.list(engagementId, entityType, entityId), [engagementId, entityType, entityId]);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    setBusy(true); setSendError(null);
    try {
      await commentsApi.create(engagementId, { entity_type: entityType, entity_id: entityId, body: body.trim() });
      setBody("");
      await reload();
    } catch (err) { setSendError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <section className="card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">Comments</h2>
      {error && <p className="mb-3 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (data?.items.length ?? 0) === 0 ? (
        <p className="text-sm text-muted">Sin comentarios.</p>
      ) : (
        <ul className="space-y-3">
          {data?.items.map((c) => (
            <li key={c.id} className="text-sm">
              <div className="flex items-baseline justify-between gap-3">
                <span className="font-medium">{c.author_name}</span>
                <span className="text-xs tabular-nums text-muted">{formatDateTime(c.created_at)}</span>
              </div>
              <p className="whitespace-pre-line leading-6">{c.body}</p>
            </li>
          ))}
        </ul>
      )}
      {can(user, "comment") && (
        <form onSubmit={submit} className="mt-4 space-y-2">
          <textarea className="input" rows={2} value={body} onChange={(e) => setBody(e.target.value)} placeholder="Escribe un comentario…" maxLength={10000} />
          {sendError && <p className="text-sm text-danger">{sendError}</p>}
          <div className="flex justify-end"><button type="submit" className="btn btn-primary" disabled={busy || !body.trim()}>Comentar</button></div>
        </form>
      )}
    </section>
  );
}
