import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { initials } from "../lib/format.ts";
import { ROLE_LABELS } from "../lib/labels";
import { useAuthStore } from "../stores/auth";
import { useEngagementStore } from "../stores/engagement";
import { useThemeStore } from "../stores/theme";

export function Header({ onMenu }: { onMenu: () => void }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { engagements, current, select } = useEngagementStore();
  const { theme, toggle } = useThemeStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    const onDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onDown);
    };
  }, [menuOpen]);

  return (
    <header className="flex h-14 items-center gap-3 border-b border-line bg-surface px-4">
      <button className="btn lg:hidden" onClick={onMenu} aria-label="Abrir menú">☰</button>
      <select
        className="input max-w-[50vw] truncate sm:max-w-xs"
        value={current?.id ?? ""}
        onChange={(e) => select(e.target.value)}
        aria-label="Engagement"
      >
        {engagements.map((e) => (
          <option key={e.id} value={e.id}>{e.name}</option>
        ))}
      </select>
      <input className="input hidden max-w-xs md:block" placeholder="Buscar (próximamente)" disabled title="Próximamente" />
      <div className="ml-auto flex items-center gap-2">
        <button
          className="btn"
          onClick={toggle}
          aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
        >
          {theme === "dark" ? "☀" : "☾"}
        </button>
        {user && (
          <div className="relative" ref={menuRef}>
            <button
              className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-xs font-semibold text-accent-ink"
              onClick={() => setMenuOpen((o) => !o)}
              aria-expanded={menuOpen}
              aria-controls="user-menu"
              aria-label="Menú de usuario"
            >
              {initials(user.full_name)}
            </button>
            {menuOpen && (
              <div id="user-menu" className="card absolute right-0 top-11 z-50 w-64 p-3">
                <div className="text-sm font-medium">{user.full_name}</div>
                <div className="mb-3 text-[11px] text-muted">{ROLE_LABELS[user.role]} · {user.organization_name}</div>
                <button
                  className="btn w-full justify-center"
                  onClick={() => logout().then(() => navigate("/login"))}
                >
                  Salir
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
