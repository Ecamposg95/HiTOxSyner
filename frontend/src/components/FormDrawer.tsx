import type { FormEvent, ReactNode } from "react";

export function FormDrawer({ open, title, onClose, onSubmit, submitting, error, children, footer, hideSubmit }: {
  open: boolean;
  title: string;
  onClose: () => void;
  onSubmit: (e: FormEvent) => void;
  submitting?: boolean;
  error?: string | null;
  children: ReactNode;
  footer?: ReactNode;
  hideSubmit?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="flex-1 bg-black/20" onClick={onClose} />
      <form onSubmit={onSubmit} className="flex h-full w-full max-w-lg flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold">{title}</h2>
          <button type="button" className="btn" onClick={onClose}>Cerrar</button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">{children}</div>
        <div className="flex items-center justify-between gap-3 border-t border-line px-5 py-3">
          <div className="text-sm text-danger">{error}</div>
          <div className="flex gap-2">
            {footer}
            {!hideSubmit && <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "Guardando…" : "Guardar"}</button>}
          </div>
        </div>
      </form>
    </div>
  );
}
