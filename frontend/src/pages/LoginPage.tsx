import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { useAuthStore } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

export function LoginPage() {
  const { status, login } = useAuthStore();
  const navigate = useNavigate();
  const { theme, toggle: toggleTheme } = useThemeStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (status === "authenticated") return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface lg:grid lg:grid-cols-2">
      <div className="relative flex flex-col justify-center bg-nav px-6 py-8 text-nav-ink lg:px-16 lg:py-0">
        <div className="font-display text-4xl lg:text-6xl">HiTO</div>
        <div className="eyebrow mt-2 text-nav-ink/60">Transformation Room</div>
        <div className="mt-6 hidden text-sm text-nav-ink/60 lg:block">Syner × HiTO</div>
      </div>
      <div className="relative flex items-center justify-center px-6 py-10">
        <button
          type="button"
          className="btn absolute right-4 top-4"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
        >
          {theme === "dark" ? "☀" : "☾"}
        </button>
        <form onSubmit={submit} className="w-full max-w-sm">
          <h1 className="font-display text-2xl">Iniciar sesión</h1>
          <div className="mt-8 space-y-4">
            <label className="block">
              <span className="label">Email</span>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
            </label>
            <label className="block">
              <span className="label">Password</span>
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
            </label>
            {error && <p className="text-sm text-danger">{error}</p>}
            <button className="btn btn-primary w-full justify-center" type="submit" disabled={busy}>Entrar</button>
          </div>
          <p className="mt-6 text-center text-xs text-muted lg:hidden">Syner × HiTO</p>
        </form>
      </div>
    </div>
  );
}
