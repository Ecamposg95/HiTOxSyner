import { FormEvent, useState } from "react";
import { errorMessage } from "../api/client";
import { documentsApi, DocumentInput } from "../api/documents";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Field, Select } from "../components/Field";
import { FormDrawer } from "../components/FormDrawer";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { formatDate } from "../lib/dates";
import { DOCUMENT_CATEGORIES, ENTITY_LABELS } from "../lib/labels";
import { can } from "../lib/roles";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import type { Document } from "../types";

const EMPTY: DocumentInput = { name: "", description: "", category: "Discovery", version: "", url: "", doc_date: null, tags: [], internal_only: false };

function parseTags(value: string): string[] {
  return value.split(",").map((t) => t.trim()).filter(Boolean).slice(0, 20);
}

export function DocumentsPage() {
  const user = useAuthStore((s) => s.user);
  const engagementId = useEngagementStore((s) => s.current?.id ?? "");
  const [category, setCategory] = useState("");
  const { data, loading, error, reload } = useResource(() => documentsApi.list(engagementId, { category: category || undefined }), [engagementId, category]);
  const writable = can(user, "write");
  const [editing, setEditing] = useState<Document | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<DocumentInput>(EMPTY);
  const [tagsText, setTagsText] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreate() { setEditing(null); setForm(EMPTY); setTagsText(""); setFormError(null); setOpen(true); }
  function openEdit(d: Document) {
    if (!writable) return;
    setEditing(d);
    setForm({ name: d.name, description: d.description, category: d.category, version: d.version, url: d.url, doc_date: d.doc_date, tags: d.tags, internal_only: d.internal_only });
    setTagsText(d.tags.join(", "));
    setFormError(null); setOpen(true);
  }
  const set = (key: keyof DocumentInput, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setFormError(null);
    const payload = { ...form, tags: parseTags(tagsText) };
    try {
      if (editing) await documentsApi.update(editing.id, payload);
      else await documentsApi.create(engagementId, payload);
      setOpen(false);
      await reload();
    } catch (err) { setFormError(errorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader eyebrow="Ejecución" title="Documents" subtitle="Repositorio del engagement: entregables, evidencia y minutas" action={writable && <button className="btn btn-primary" onClick={openCreate}>Nuevo documento</button>} />
      <div className="mb-4 w-48"><Select value={category} onChange={setCategory} options={DOCUMENT_CATEGORIES} allowEmpty="Todas las categorías" /></div>
      {error && <p className="mb-4 text-sm text-danger">{error}</p>}
      {loading && !data ? <p className="text-sm text-muted">Cargando…</p> : (
        <DataTable<Document>
          rows={data?.items ?? []}
          onRowClick={writable ? openEdit : undefined}
          empty={<EmptyState title="Sin documentos" hint={writable ? "Registra el primer documento del engagement." : undefined} />}
          columns={[
            { key: "name", header: "Documento", render: (d) => (
              <span className="font-medium">
                {d.url ? <a href={d.url} target="_blank" rel="noreferrer" className="hover:underline" onClick={(e) => e.stopPropagation()}>{d.name}</a> : d.name}
                <span className="block text-xs text-muted">{d.category}{d.version ? ` · v${d.version}` : ""}</span>
              </span>
            ) },
            { key: "date", header: "Fecha", render: (d) => formatDate(d.doc_date), className: "tabular-nums" },
            { key: "tags", header: "Tags", render: (d) => <span className="text-xs text-muted">{d.tags.join(", ") || "—"}</span> },
            { key: "links", header: "Vinculado a", render: (d) => <span className="text-xs text-muted">{d.links.length === 0 ? "—" : d.links.map((l) => ENTITY_LABELS[l.entity_type] ?? l.entity_type).join(", ")}</span> },
            { key: "visibility", header: "Visibilidad", render: (d) => d.internal_only ? <StatusBadge value="Interno" /> : <span className="text-xs text-muted">Compartido</span> },
          ]}
        />
      )}
      <FormDrawer open={open} title={editing ? "Editar documento" : "Nuevo documento"} onClose={() => setOpen(false)} onSubmit={submit} submitting={busy} error={formError}>
        <Field label="Nombre"><input className="input" value={form.name ?? ""} onChange={(e) => set("name", e.target.value)} required maxLength={200} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Categoría"><Select value={form.category ?? "Discovery"} onChange={(v) => set("category", v)} options={DOCUMENT_CATEGORIES} /></Field>
          <Field label="Versión"><input className="input" value={form.version ?? ""} onChange={(e) => set("version", e.target.value)} maxLength={50} /></Field>
          <Field label="Fecha del documento"><input className="input" type="date" value={form.doc_date ?? ""} onChange={(e) => set("doc_date", e.target.value || null)} /></Field>
          <Field label="Visibilidad">
            <Select value={form.internal_only ? "Solo Syner" : "Compartido con el cliente"} onChange={(v) => set("internal_only", v === "Solo Syner")} options={["Compartido con el cliente", "Solo Syner"]} />
          </Field>
        </div>
        <Field label="URL"><input className="input" type="url" value={form.url ?? ""} onChange={(e) => set("url", e.target.value)} maxLength={2000} placeholder="https://" /></Field>
        <Field label="Tags (separados por coma)"><input className="input" value={tagsText} onChange={(e) => setTagsText(e.target.value)} /></Field>
        <Field label="Descripción"><textarea className="input" rows={3} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} /></Field>
      </FormDrawer>
    </>
  );
}
