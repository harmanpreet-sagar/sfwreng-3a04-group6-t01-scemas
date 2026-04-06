/**
 * Login page — operator entry; styled to match the public site (ink + parchment + display type).
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { ScemasLogoMark } from '../components/ScemasLogoMark';

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(email.trim(), password);
      if (!res.identity_verified) {
        setError('Login failed. Check your credentials.');
        return;
      }
      signIn(res.account, res.access_token ?? null);
      navigate('/thresholds', { replace: true });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Could not connect to the server.';
      setError(typeof msg === 'string' ? msg : 'Login failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-parchment bg-noise-soft px-4 py-10 sm:px-6 text-ink-900">
      <div className="relative z-10 w-full max-w-md">
        <div className="rounded-2xl border border-ink-200/70 bg-white/90 p-8 shadow-card-lg backdrop-blur-sm">
          <div className="text-center border-b border-ink-100 pb-8 mb-8">
            <Link
              to="/"
              className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-moss-700 text-white shadow-md shadow-moss-900/15 ring-2 ring-moss-500/20 mb-5 transition hover:bg-moss-600 hover:ring-moss-400/35"
            >
              <ScemasLogoMark className="w-8 h-8" />
            </Link>
            <h1 className="font-display text-4xl font-bold text-ink-950 tracking-tight">SCEMAS</h1>
            <p className="text-moss-800 text-xs font-bold uppercase tracking-[0.25em] mt-3">Operator access</p>
          </div>

          <div className="mb-6">
            <h2 className="font-display text-2xl font-bold text-ink-950 tracking-tight">Welcome back</h2>
            <p className="text-sm text-ink-600 mt-1.5">Sign in to thresholds, alerts, and maps.</p>
          </div>

          {error && (
            <div className="mb-5 rounded-xl bg-red-50 border border-red-200/80 px-4 py-3 text-sm text-red-900 flex items-start gap-3">
              <svg className="w-5 h-5 shrink-0 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
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
              <label htmlFor="password" className="label">
                Password
              </label>
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

            <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 text-base mt-2">
              {loading ? (
                <>
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Signing in…
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <div className="mt-8 rounded-xl bg-parchment-deep border border-ink-200/60 p-4 space-y-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-ink-500">Demo accounts</p>
            <div className="space-y-2 text-xs text-ink-700">
              <p>
                <span className="font-bold text-ink-950">Admin</span>{' '}
                <span className="font-mono text-[11px]">admin@demo.com</span> /{' '}
                <span className="font-mono text-[11px]">admin123</span>
              </p>
              <p>
                <span className="font-bold text-ink-950">Operator</span>{' '}
                <span className="font-mono text-[11px]">operator@demo.com</span> /{' '}
                <span className="font-mono text-[11px]">operator123</span>
              </p>
            </div>
          </div>
        </div>

        <p className="mt-8 text-center text-xs text-ink-500">
          <Link
            to="/"
            className="font-semibold text-moss-800 hover:text-moss-950 underline-offset-2 hover:underline"
          >
            ← Public site
          </Link>
          <span className="mx-2 text-ink-400">·</span>
          <span className="text-ink-500">SE 3A04 · Group 6</span>
        </p>
      </div>
    </div>
  );
}
