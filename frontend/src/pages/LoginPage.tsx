import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import { useAuthStore } from "../stores/auth";

export function LoginPage() {
  const { status, login } = useAuthStore();
  const navigate = useNavigate();
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
    <div className="flex min-h-screen items-center justify-center bg-white px-4">
      <form onSubmit={submit} className="w-full max-w-sm">
        <div className="text-xs font-semibold tracking-[0.3em]">SYNER × HiTO</div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Transformation Room</h1>
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
          <button className="btn btn-primary w-full justify-center" type="submit" disabled={busy}>Sign in</button>
        </div>
        <p className="mt-6 text-center text-xs text-muted">Private advisory workspace</p>
      </form>
    </div>
  );
}
