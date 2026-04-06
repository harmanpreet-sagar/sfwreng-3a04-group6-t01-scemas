/**
 * Public marketing entry for SCEMAS: editorial layout, warm palette, live map when API key is set.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import PublicLandingMap from '../components/PublicLandingMap';
import PublicZoneStatusCards from '../components/PublicZoneStatusCards';
import { ScemasLogoMark } from '../components/ScemasLogoMark';
import {
  fetchPublicZones,
  isPublicApiConfigured,
  type PublicZoneSummary,
} from '../api/publicZones';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const DOCS_URL = `${API_BASE.replace(/\/$/, '')}/docs`;

const PUBLIC_ENDPOINTS = [
  {
    method: 'GET',
    path: '/public/zones',
    summary: 'List all zones with latest aggregated metrics and high-level status (normal vs alerting).',
  },
  {
    method: 'GET',
    path: '/public/zones/{zone}',
    summary: 'Same summary for a single zone, useful for signage or kiosks.',
  },
] as const;

const PILLARS = [
  {
    title: 'Validated telemetry',
    body: 'MQTT ingest with range checks before anything hits your dashboards or public feeds.',
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    ),
  },
  {
    title: 'Zone intelligence',
    body: 'City zones roll up to averages and peaks operators can act on, not raw sensor noise.',
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
    ),
  },
  {
    title: 'Thresholds & alerts',
    body: 'Rules you define drive operational alerts; staff sign in to acknowledge and resolve.',
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0" />
    ),
  },
] as const;

export default function LandingPage() {
  const [publicZones, setPublicZones] = useState<PublicZoneSummary[] | null>(null);
  const [liveAttempted, setLiveAttempted] = useState(false);

  useEffect(() => {
    if (!isPublicApiConfigured()) {
      setLiveAttempted(true);
      return;
    }
    let cancelled = false;
    void (async () => {
      const data = await fetchPublicZones();
      if (!cancelled) {
        setPublicZones(data ?? null);
        setLiveAttempted(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const liveLabel: string | null = !isPublicApiConfigured()
    ? null
    : !liveAttempted
      ? 'Loading public summaries…'
      : publicZones && publicZones.length > 0
        ? 'Live data from the public API.'
        : 'Public API unreachable; coverage map only.';

  return (
    <div className="min-h-screen bg-parchment bg-noise-soft text-ink-900">
      <header className="sticky top-0 z-50 border-b border-ink-900/10 bg-parchment/85 backdrop-blur-lg">
        <div className="mx-auto flex h-[4.25rem] max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-3 min-w-0 group">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-moss-700 text-white shadow-md shadow-moss-900/15 ring-2 ring-moss-500/20 transition group-hover:ring-moss-400/35">
              <ScemasLogoMark className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <span className="font-display text-lg font-bold tracking-tight text-ink-950 block leading-none">SCEMAS</span>
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-moss-600">McMaster · Group 6</span>
            </div>
          </Link>
          <nav className="flex items-center gap-1 sm:gap-2 shrink-0">
            <a
              href={DOCS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden rounded-xl px-3 py-2 text-sm font-semibold text-ink-600 transition hover:bg-ink-900/5 sm:inline-block"
            >
              API reference
            </a>
            <a
              href="#public-api"
              className="rounded-xl px-3 py-2 text-sm font-semibold text-ink-600 transition hover:bg-ink-900/5"
            >
              Developers
            </a>
            <Link
              to="/login"
              className="rounded-xl bg-moss-700 px-4 py-2.5 text-sm font-bold text-white shadow-md shadow-moss-900/20 transition hover:bg-moss-600"
            >
              Operator sign-in
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-ink-200/70 bg-white/90">
          <div className="pointer-events-none absolute inset-0 bg-noise-soft opacity-[0.35]" aria-hidden />
          <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:py-28">
            <p className="eyebrow text-moss-800">Environmental monitoring</p>
            <h1 className="font-display mt-4 max-w-3xl text-[2.35rem] font-bold leading-[1.08] tracking-tight text-ink-950 sm:text-5xl lg:text-[3.25rem]">
              Air, noise, and climate signals made legible for cities.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-ink-600 leading-relaxed">
              SCEMAS ingests sensor streams, validates what is real, and publishes zone-level summaries. Residents see the
              story; operators get thresholds, alerts, and audit trails.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link
                to="/login"
                className="inline-flex items-center justify-center rounded-xl bg-moss-700 px-6 py-3.5 text-sm font-bold text-white shadow-md shadow-moss-900/20 transition hover:bg-moss-600"
              >
                Open Dashboard
              </Link>
              <a
                href="#map"
                className="inline-flex items-center justify-center rounded-xl border border-ink-300/90 bg-white px-6 py-3.5 text-sm font-semibold text-ink-800 shadow-sm transition hover:border-moss-300 hover:bg-moss-50/80"
              >
                View coverage map
              </a>
            </div>
            <div className="mt-14 grid grid-cols-3 gap-6 border-t border-ink-200/80 pt-10 sm:max-w-lg">
              {[
                { n: '4', l: 'Zones' },
                { n: '4', l: 'Metrics' },
                { n: '1', l: 'Public API' },
              ].map(s => (
                <div key={s.l}>
                  <p className="font-display text-3xl font-bold text-ink-950 sm:text-4xl">{s.n}</p>
                  <p className="text-xs font-semibold uppercase tracking-widest text-ink-500">{s.l}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pillars */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <div className="max-w-2xl">
            <p className="section-title">How it fits together</p>
            <h2 className="font-display mt-2 text-3xl font-bold tracking-tight text-ink-950 sm:text-4xl">
              From raw readings to decisions
            </h2>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {PILLARS.map(p => (
              <div
                key={p.title}
                className="group relative overflow-hidden rounded-2xl border border-ink-200/80 bg-white p-6 shadow-card transition duration-300 hover:border-moss-300/60 hover:shadow-lift"
              >
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-moss-50 text-moss-700 ring-1 ring-moss-200/80 transition group-hover:bg-moss-100">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {p.icon}
                  </svg>
                </div>
                <h3 className="font-display text-lg font-bold text-ink-950">{p.title}</h3>
                <p className="mt-2 text-sm text-ink-600 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Map + aside */}
        <section id="map" className="border-y border-ink-200/60 bg-parchment-deep/80 py-16 sm:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid gap-10 lg:grid-cols-5 lg:items-start">
              <div className="lg:col-span-3">
                <p className="section-title">Live layer</p>
                <h2 className="font-display mt-2 text-2xl font-bold text-ink-950 sm:text-3xl">Monitoring coverage</h2>
                {liveLabel != null ? (
                  <p className="mt-2 text-sm text-ink-600 max-w-prose">{liveLabel}</p>
                ) : null}
                <div className="mt-5 overflow-hidden rounded-2xl border border-ink-200/90 bg-white shadow-card-lg ring-1 ring-ink-900/[0.04]">
                  <PublicLandingMap zones={publicZones} />
                </div>
                <p className="mt-3 text-xs text-ink-500 leading-relaxed max-w-prose">
                  Hamilton / McMaster centroid. Teal markers reflect healthy summaries; orange and red hint at public-facing
                  alert severity when the API is wired.
                </p>
              </div>
              <aside className="lg:col-span-2">
                <div className="sticky top-24 rounded-2xl border border-ink-200/80 bg-white/95 p-8 shadow-card-lg backdrop-blur-sm">
                  <p className="text-moss-800 text-xs font-bold uppercase tracking-[0.2em]">Operators</p>
                  <h3 className="font-display mt-3 text-2xl font-bold leading-snug text-ink-950">
                    Threshold rules & alert desk
                  </h3>
                  <ul className="mt-6 space-y-4 text-sm text-ink-600">
                    <li className="flex gap-3">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                      Role-based access: admins edit rules; operators monitor and resolve.
                    </li>
                    <li className="flex gap-3">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-moss-500" />
                      Charts and map stay in sync with the same threshold catalogue.
                    </li>
                    <li className="flex gap-3">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400" />
                      SSE pushes new violations to the dashboard in near real time.
                    </li>
                  </ul>
                  <Link
                    to="/login"
                    className="mt-8 flex w-full items-center justify-center rounded-xl border border-moss-600/50 bg-moss-700 py-3.5 text-sm font-bold text-white transition hover:bg-moss-600"
                  >
                    Sign in to Dashboard →
                  </Link>
                </div>
              </aside>
            </div>

            <div className="mt-10">
              <p className="section-title">Public summary</p>
              <h3 className="font-display mt-2 text-2xl font-bold text-ink-950">Zone status cards</h3>
              <p className="mt-2 max-w-2xl text-sm text-ink-600">
                Each card shows the current AQI label and latest public metric values for one zone.
              </p>
              <div className="mt-6">
                <PublicZoneStatusCards zones={publicZones} />
              </div>
            </div>
          </div>
        </section>

        {/* Public API */}
        <section id="public-api" className="py-16 sm:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-2xl">
                <p className="section-title">Integrations</p>
                <h2 className="font-display mt-2 text-3xl font-bold text-ink-950 sm:text-4xl">Public API</h2>
                <p className="mt-3 text-ink-600 leading-relaxed">
                  Read-only JSON for signage, research, and partner apps. Authenticate with{' '}
                  <code className="rounded-lg bg-parchment-muted px-2 py-0.5 text-xs font-mono text-ink-800">
                    Authorization: Bearer &lt;api_key&gt;
                  </code>
                  . Rate limits apply per key.
                </p>
              </div>
              <a
                href={DOCS_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex shrink-0 items-center justify-center rounded-xl bg-moss-600 px-6 py-3.5 text-sm font-bold text-white shadow-md hover:bg-moss-500"
              >
                Browse OpenAPI docs
              </a>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {PUBLIC_ENDPOINTS.map(ep => (
                <div
                  key={ep.path}
                  className="rounded-2xl border border-ink-200/80 bg-white p-6 shadow-card transition hover:border-moss-200"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-lg bg-moss-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-moss-800">
                      {ep.method}
                    </span>
                    <code className="text-sm font-mono font-semibold text-ink-900">{ep.path}</code>
                  </div>
                  <p className="mt-4 text-sm text-ink-600 leading-relaxed">{ep.summary}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <footer className="border-t border-ink-200/80 bg-parchment-deep/90 py-12 text-ink-900">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-display text-xl font-bold text-ink-950">SCEMAS</p>
                <p className="mt-2 max-w-sm text-sm text-ink-600 leading-relaxed">
                  Software Design II: Smart City Environmental Monitoring &amp; Alert System. Zone summaries only in public
                  views; no PII in telemetry paths we expose.
                </p>
              </div>
              <div className="text-sm text-ink-600">
                <p className="font-semibold text-ink-800">Course</p>
                <p className="mt-1">SE 3A04 · Tutorial 01 · Group 6</p>
              </div>
            </div>
            <p className="mt-10 border-t border-ink-200/70 pt-8 text-center text-xs text-ink-500">
              Built for demonstration, not a production security posture.
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
