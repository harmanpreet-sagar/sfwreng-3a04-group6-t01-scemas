/**
 * Login page — the single entry point for all users.
 *
 * Flow:
 *  1. User submits email + password.
 *  2. We POST to /account/login (see api/auth.ts).
 *  3. On success the backend returns the account profile and a signed JWT.
 *  4. signIn() writes both to AuthContext (and to localStorage for persistence).
 *  5. We navigate to /thresholds; RequireAuth in App.tsx will permit entry.
 *
 * Error handling:
 *  - A 401 from the backend returns a FastAPI detail string which we surface
 *    directly ("email or password incorrect, or account inactive").
 *  - A network failure (Docker not running, wrong port) shows a generic
 *    "Could not connect to the server" message rather than an axios stack trace.
 *  - identity_verified being false with a 200 response is a defensive check;
 *    the current backend always raises 401 on failure rather than returning false,
 *    but we handle both to stay robust against future changes.
 *
 * Demo credentials are shown in plain text at the bottom of the card because
 * this is a prototype demo, not a production deployment.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate   = useNavigate();

  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState<string | null>(null);
  const [loading,  setLoading]  = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Trim whitespace from the email — a common source of "wrong password"
      // errors when users copy-paste the demo credentials with trailing spaces.
      const res = await login(email.trim(), password);
      if (!res.identity_verified) {
        setError('Login failed. Check your credentials.');
        return;
      }
      // access_token may be null if JWT_SECRET is not set in the backend env.
      // In that case signIn stores null, setAuthToken is skipped, and the user
      // will hit 401 on the first protected API call (triggering a sign-out).
      signIn(res.account, res.access_token ?? null);
      navigate('/thresholds', { replace: true });
    } catch (err: unknown) {
      // Prefer the FastAPI detail string; fall back to a generic message.
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Could not connect to the server.';
      setError(typeof msg === 'string' ? msg : 'Login failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-slate-950 p-4 sm:p-6">
      {/* Ambient background */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_120%_80%_at_50%_-20%,rgba(20,184,166,0.35),transparent)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -left-32 top-1/4 h-96 w-96 rounded-full bg-teal-500/20 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-24 bottom-0 h-80 w-80 rounded-full bg-cyan-600/15 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:48px_48px]"
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-teal-600 shadow-lg shadow-teal-900/40 ring-1 ring-white/10 mb-5">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">SCEMAS</h1>
          <p className="text-teal-200/90 text-sm mt-1.5 font-medium">Smart Campus Environmental Monitoring</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.97] p-8 shadow-card-lg backdrop-blur-md">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Welcome back</h2>
            <p className="text-sm text-slate-500 mt-1">Sign in to manage threshold rules</p>
          </div>

          {error && (
            <div className="mb-5 rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-800 flex items-start gap-3">
              <svg className="w-5 h-5 shrink-0 text-red-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="label">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@demo.com"
                className="input"
              />
            </div>

            <div>
              <label htmlFor="password" className="label">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 text-base mt-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Signing in…
                </>
              ) : 'Sign in'}
            </button>
          </form>

          <div className="mt-8 rounded-xl bg-slate-50 border border-slate-100 p-4 space-y-2">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Demo accounts</p>
            <div className="space-y-1.5 text-xs text-slate-600">
              <p>
                <span className="font-semibold text-slate-800">Admin</span>
                {' — '}
                <span className="font-mono text-[11px] sm:text-xs">admin@demo.com</span>
                {' / '}
                <span className="font-mono text-[11px] sm:text-xs">admin123</span>
              </p>
              <p>
                <span className="font-semibold text-slate-800">Operator</span>
                {' — '}
                <span className="font-mono text-[11px] sm:text-xs">operator@demo.com</span>
                {' / '}
                <span className="font-mono text-[11px] sm:text-xs">operator123</span>
              </p>
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-slate-500">
          McMaster SCEMAS · Group 6 Tutorial 01
        </p>
      </div>
    </div>
  );
}
