import { useNavigate } from "react-router-dom";
import { ROLE_LABELS } from "../lib/labels";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";

export function Header({ onMenu }: { onMenu: () => void }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { engagements, current, select } = useEngagementStore();
  const navigate = useNavigate();

  return (
    <header className="flex h-14 items-center gap-3 border-b border-line bg-white px-4">
      <button className="btn lg:hidden" onClick={onMenu} aria-label="Abrir menú">☰</button>
      <select
        className="input max-w-xs"
        value={current?.id ?? ""}
        onChange={(e) => select(e.target.value)}
        aria-label="Engagement"
      >
        {engagements.map((e) => (
          <option key={e.id} value={e.id}>{e.name}</option>
        ))}
      </select>
      <input className="input hidden max-w-xs md:block" placeholder="Buscar (próximamente)" disabled title="Próximamente" />
      <div className="ml-auto flex items-center gap-3">
        <button className="btn" disabled title="Notificaciones (próximamente)" aria-label="Notificaciones">○</button>
        {user && (
          <div className="text-right leading-tight">
            <div className="text-sm font-medium">{user.full_name}</div>
            <div className="text-[11px] text-muted">{ROLE_LABELS[user.role]} · {user.organization_name}</div>
          </div>
        )}
        <button className="btn" onClick={() => logout().then(() => navigate("/login"))}>Salir</button>
      </div>
    </header>
  );
}
