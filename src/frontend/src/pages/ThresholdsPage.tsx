/**
 * ThresholdsPage — the main dashboard of the SCEMAS threshold management UI.
 *
 * Layout (top → bottom):
 *  1. Navigation bar  — displays the logged-in user's name / clearance and a sign-out button.
 *  2. OPERATOR banner — shown only when clearance is not "admin" to explain read-only access.
 *  3. Stats row       — four summary cards (total rules, active, critical, zones covered).
 *  4. Map + Chart row — ZoneMap (Leaflet) left, SeverityChart (Recharts) right.
 *  5. Table card      — filterable list of all threshold rules with inline CRUD actions.
 *  6. ThresholdFormModal (overlay) — shown when creating or editing a rule.
 *
 * State management philosophy:
 *  - `thresholds` is the canonical list fetched from the backend. All derived
 *    views (stats, chart data, map markers, table rows) are computed from it —
 *    there is no separate "local copy". CRUD handlers update this single array
 *    optimistically rather than triggering a full refetch to avoid flicker.
 *  - `filter` and `selectedZone` are kept in sync bidirectionally: clicking a
 *    zone marker on the map updates the zone dropdown, and changing the zone
 *    dropdown highlights the corresponding marker.
 *
 * Authentication / RBAC:
 *  - A 401 response to listThresholds (e.g. expired token) automatically signs
 *    the user out and redirects to /login rather than leaving them on a broken page.
 *  - isAdmin gates the "New rule" button, the Edit/Delete actions in the table,
 *    and the active toggle. Operators see the same data but cannot modify it.
 *
 * z-index note: the map card uses the `isolate` Tailwind class which creates
 * a new CSS stacking context. This confines Leaflet's internal z-indices
 * (which go up to ~700) so that the ThresholdFormModal at z-[1000] always
 * renders on top of the map when opened.
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listThresholds, createThreshold, updateThreshold,
  activateThreshold, deactivateThreshold, deleteThreshold,
} from '../api/thresholds';
import { listAlerts } from '../api/alerts';
import { getAggregationHistory, getAggregationZones } from '../api/aggregation';
import { getValidationStatus } from '../api/validation';
import { API_BASE } from '../api/client';
import { openAlertSseStream } from '../lib/sseAlerts';
import { useAuth } from '../context/AuthContext';
import type {
  AggregationHistoryResponse,
  AggregationZoneSummary,
  Alert,
  SseAlertEvent,
  Threshold,
  ThresholdCreate,
  ValidationStatusResponse,
} from '../types';
import ThresholdTable from '../components/ThresholdTable';
import ThresholdFormModal from '../components/ThresholdFormModal';
import SeverityChart from '../components/SeverityChart';
import ZoneMap from '../components/ZoneMap';
import ViolationAlertModal from '../components/ViolationAlertModal';
import AlertsBrowserModal from '../components/AlertsBrowserModal';
import AggregationHistoryChart from '../components/AggregationHistoryChart';
import MetricGauge from '../components/MetricGauge';
import PipelineHealthIndicator from '../components/PipelineHealthIndicator';
import { ScemasLogoMark } from '../components/ScemasLogoMark';
import { KNOWN_METRICS } from '../types';

type Filter = { zone: string; metric: string; status: 'all' | 'active' | 'inactive' };

export default function ThresholdsPage() {
  const { account, token, isAdmin, signOut } = useAuth();
  const navigate = useNavigate();

  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [alertsError, setAlertsError] = useState<string | null>(null);
  const [showAlertsBrowser, setShowAlertsBrowser] = useState(false);
  const [browserInitialShowAll, setBrowserInitialShowAll] = useState(false);
  const [violationQueue, setViolationQueue] = useState<SseAlertEvent[]>([]);
  const [aggregationZones, setAggregationZones] = useState<AggregationZoneSummary[]>([]);
  const [aggregationLoading, setAggregationLoading] = useState(true);
  const [aggregationError, setAggregationError] = useState<string | null>(null);
  const [validationStatus, setValidationStatus] = useState<ValidationStatusResponse | null>(null);
  const [validationLoading, setValidationLoading] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [chartZone, setChartZone] = useState('zone-a');
  const [chartMetric, setChartMetric] = useState('aqi');
  const [gaugeZone, setGaugeZone] = useState('zone-a');
  const [gaugeMetric, setGaugeMetric] = useState('aqi');
  const [historyData, setHistoryData] = useState<AggregationHistoryResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // filter drives both the zone map selection highlight and the table rows shown.
  const [filter, setFilter] = useState<Filter>({ zone: '', metric: '', status: 'all' });
  // selectedZone mirrors filter.zone but is kept separate so ZoneMap can deselect
  // by passing '' when the same zone is clicked twice (toggle behaviour).
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  const [showForm,   setShowForm]   = useState(false);
  // editTarget is null when creating a new rule and non-null when editing an existing one.
  const [editTarget, setEditTarget] = useState<Threshold | null>(null);

  // ── Load thresholds ──────────────────────────────────────────────────────────
  // useCallback so that reload's identity is stable across renders — needed because
  // it is listed in the useEffect dependency array below.
  const reload = useCallback(async () => {
    setFetchError(null);
    try {
      const data = await listThresholds();
      setThresholds(data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      // A 401 means the JWT has expired or was never issued (missing JWT_SECRET).
      // Sign out and redirect rather than showing an error message that the user
      // cannot resolve without logging back in.
      if ((err as { response?: { status?: number } })?.response?.status === 401) {
        signOut();
        navigate('/login', { replace: true });
        return;
      }
      setFetchError(detail ?? 'Failed to load thresholds.');
    } finally {
      setLoading(false);
    }
  }, [signOut, navigate]);

  useEffect(() => { void reload(); }, [reload]);

  const loadAlerts = useCallback(async () => {
    setAlertsLoading(true);
    setAlertsError(null);
    try {
      const { alerts: rows } = await listAlerts();
      setAlerts(rows);
    } catch (err: unknown) {
      if ((err as { response?: { status?: number } })?.response?.status === 401) {
        signOut();
        navigate('/login', { replace: true });
        return;
      }
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setAlertsError(typeof detail === 'string' ? detail : 'Failed to load alerts.');
    } finally {
      setAlertsLoading(false);
    }
  }, [signOut, navigate]);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  useEffect(() => {
    const id = window.setInterval(() => {
      void loadAlerts();
    }, 10_000);
    return () => window.clearInterval(id);
  }, [loadAlerts]);

  const loadAggregationZones = useCallback(async () => {
    setAggregationLoading(true);
    setAggregationError(null);
    try {
      const data = await getAggregationZones();
      setAggregationZones(data.zones);
    } catch (err: unknown) {
      if ((err as { response?: { status?: number } })?.response?.status === 401) {
        signOut();
        navigate('/login', { replace: true });
        return;
      }
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setAggregationError(typeof detail === 'string' ? detail : 'Failed to load aggregate summaries.');
    } finally {
      setAggregationLoading(false);
    }
  }, [navigate, signOut]);

  const loadValidationStatus = useCallback(async () => {
    setValidationLoading(true);
    setValidationError(null);
    try {
      const data = await getValidationStatus();
      setValidationStatus(data);
    } catch {
      setValidationError('Failed to load pipeline health.');
    } finally {
      setValidationLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAggregationZones();
    void loadValidationStatus();
  }, [loadAggregationZones, loadValidationStatus]);

  useEffect(() => {
    const id = window.setInterval(() => {
      void loadAggregationZones();
      void loadValidationStatus();
    }, 30_000);
    return () => window.clearInterval(id);
  }, [loadAggregationZones, loadValidationStatus]);

  useEffect(() => {
    if (!aggregationZones.length) return;
    const zoneIds = aggregationZones.map(z => z.zone);
    if (!zoneIds.includes(chartZone)) setChartZone(zoneIds[0]);
    if (!zoneIds.includes(gaugeZone)) setGaugeZone(zoneIds[0]);
  }, [aggregationZones, chartZone, gaugeZone]);

  const loadHistory = useCallback(async () => {
    if (!chartZone || !chartMetric) return;
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const data = await getAggregationHistory(chartZone, chartMetric, 24);
      setHistoryData(data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setHistoryError(typeof detail === 'string' ? detail : 'Failed to load aggregation history.');
    } finally {
      setHistoryLoading(false);
    }
  }, [chartMetric, chartZone]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    const id = window.setInterval(() => {
      void loadHistory();
    }, 30_000);
    return () => window.clearInterval(id);
  }, [loadHistory]);

  const handleSseAlert = useCallback(
    (evt: SseAlertEvent) => {
      if (evt.event_type === 'alert.created') {
        setViolationQueue(q => (q.some(x => x.id === evt.id) ? q : [...q, evt]));
      }
      void loadAlerts();
    },
    [loadAlerts],
  );

  useEffect(() => {
    if (!token) return;
    const authToken = token;
    const ac = new AbortController();
    let cancelled = false;

    async function streamLoop() {
      while (!cancelled && !ac.signal.aborted) {
        try {
          await openAlertSseStream(API_BASE, authToken, handleSseAlert, ac.signal);
        } catch {
          /* network drop or abort */
        }
        if (cancelled || ac.signal.aborted) break;
        await new Promise(r => setTimeout(r, 4000));
      }
    }
    void streamLoop();
    return () => {
      cancelled = true;
      ac.abort();
    };
  }, [token, handleSseAlert]);

  const activeAlertCount = alerts.filter(a => a.status === 'active').length;
  const currentViolation = violationQueue[0] ?? null;
  const selectedAggregationZone =
    aggregationZones.find(z => z.zone === selectedZone) ?? aggregationZones[0] ?? null;
  const gaugeZoneSummary =
    aggregationZones.find(z => z.zone === gaugeZone) ?? aggregationZones[0] ?? null;
  const currentGaugeMetric =
    gaugeZoneSummary?.metrics.find(m => m.metric === gaugeMetric)
    ?? gaugeZoneSummary?.metrics[0]
    ?? null;
  const availableZones = aggregationZones.map(z => z.zone);

  // ── CRUD handlers ────────────────────────────────────────────────────────────
  // Handlers receive the minimal payload from the form/table and delegate
  // the actual HTTP call to the API module. On success they patch the local
  // `thresholds` array in-place — no full refetch required.

  async function handleSave(data: ThresholdCreate) {
    if (editTarget) {
      // Strip is_active from the PATCH body: active state must be changed via
      // the dedicated /activate and /deactivate routes so the audit log is populated.
      const { is_active: _ia, ...changes } = data;
      const updated = await updateThreshold(editTarget.id, changes);
      setThresholds(prev => prev.map(t => t.id === updated.id ? updated : t));
    } else {
      const created = await createThreshold(data);
      setThresholds(prev => [...prev, created]);
    }
  }

  async function handleToggle(t: Threshold) {
    // The backend returns the updated threshold so the UI reflects the DB value
    // rather than optimistically flipping the local flag.
    const updated = t.is_active
      ? await deactivateThreshold(t.id)
      : await activateThreshold(t.id);
    setThresholds(prev => prev.map(r => r.id === updated.id ? updated : r));
  }

  async function handleDelete(id: number) {
    await deleteThreshold(id);
    // Remove optimistically — a failure would have thrown and the row stays.
    setThresholds(prev => prev.filter(t => t.id !== id));
  }

  function openEdit(t: Threshold) {
    setEditTarget(t);
    setShowForm(true);
  }

  function openCreate() {
    setEditTarget(null); // ensure form starts blank, not pre-populated
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditTarget(null);
  }

  // ── Zone-map click syncs with table filter ───────────────────────────────────
  // Clicking a zone on the map filters the table to that zone. Clicking the
  // same zone again deselects it (zone === selectedZone → empty string clears filter).
  function handleZoneClick(zone: string) {
    setSelectedZone(zone || null);
    if (zone) {
      setChartZone(zone);
      setGaugeZone(zone);
    }
    setFilter(f => ({ ...f, zone: zone }));
  }

  // ── Derived filtered list ────────────────────────────────────────────────────
  // Computed inline so no stale state is possible. The filter short-circuits
  // on the first failing condition to keep iteration fast for large lists.
  const visible = thresholds.filter(t => {
    if (filter.zone   && t.zone   !== filter.zone)   return false;
    if (filter.metric && t.metric !== filter.metric)  return false;
    if (filter.status === 'active'   && !t.is_active)  return false;
    if (filter.status === 'inactive' &&  t.is_active)  return false;
    return true;
  });

  // ── Stats ────────────────────────────────────────────────────────────────────
  // All stats are derived from the full (unfiltered) thresholds array so the
  // numbers always reflect the system-wide state, not the current filter view.
  const totalActive   = thresholds.filter(t => t.is_active).length;
  const totalCritical = thresholds.filter(t => t.severity === 'critical').length;

  // Unique zone / metric lists power the filter dropdowns and show only values
  // that actually exist in the current data, avoiding dead filter options.
  const uniqueZones   = [...new Set(thresholds.map(t => t.zone))].sort();
  const uniqueMetrics = [...new Set(thresholds.map(t => t.metric))].sort();

  return (
    <div className="min-h-screen flex flex-col bg-parchment bg-noise-soft">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-gradient-to-r from-moss-800 via-moss-800 to-moss-900 text-white shadow-lg shadow-moss-900/35">
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" aria-hidden />
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 h-[4.25rem] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-2xl bg-white text-moss-700 flex items-center justify-center shadow-lg shadow-moss-950/25 shrink-0 ring-2 ring-white/25">
              <ScemasLogoMark className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <span className="font-display font-bold tracking-tight text-lg block leading-tight">SCEMAS</span>
              <span className="hidden sm:block text-moss-200/90 text-[10px] font-bold uppercase tracking-[0.2em]">Operator Dashboard</span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <button
              type="button"
              onClick={() => {
                setBrowserInitialShowAll(false);
                setShowAlertsBrowser(true);
                void loadAlerts();
              }}
              className="relative inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm font-semibold text-white hover:bg-white/10 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-moss-200"
            >
              <svg className="w-4 h-4 opacity-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
                />
              </svg>
              Alerts
              {activeAlertCount > 0 && (
                <span className="flex h-5 min-w-[1.25rem] items-center justify-center rounded-md bg-red-500 px-1 text-[11px] font-bold tabular-nums text-white shadow-sm">
                  {activeAlertCount > 99 ? '99+' : activeAlertCount}
                </span>
              )}
            </button>
            <span className="hidden md:block text-sm text-moss-100/95 truncate max-w-[200px]">
              {account?.name}
              <span
                className={`ml-2 text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-md font-bold
                ${isAdmin ? 'bg-moss-600/40 text-moss-100 ring-1 ring-moss-400/30' : 'bg-moss-900/70 text-moss-200 ring-1 ring-white/15'}`}
              >
                {account?.clearance}
              </span>
            </span>
            <button
              type="button"
              onClick={() => { signOut(); navigate('/login', { replace: true }); }}
              className="rounded-xl px-3 py-2 text-sm font-semibold text-moss-100/90 hover:text-white hover:bg-white/10 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-moss-200"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-10 space-y-10">

        {/* ── OPERATOR read-only banner ───────────────────────────────────────
            Shown proactively so operators understand why they cannot see the
            "New rule" button or toggle switches before they go looking for them. */}
        {!isAdmin && (
          <div className="rounded-2xl border border-moss-300/50 bg-gradient-to-r from-moss-100/60 to-parchment px-4 py-4 flex items-center gap-3 text-sm text-ink-900 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-moss-700 text-white">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
            </div>
            <span>
              Signed in as <strong>OPERATOR</strong> — read-only thresholds. Alerts and maps stay available; rule changes require an admin.
            </span>
          </div>
        )}

        {/* ── Stats row ──────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          {[
            { label: 'Total rules', value: thresholds.length, accent: 'from-sky-600 to-blue-700', text: 'text-sky-800' },
            { label: 'Active', value: totalActive, accent: 'from-moss-500 to-moss-700', text: 'text-moss-800' },
            { label: 'Critical', value: totalCritical, accent: 'from-rose-600 to-red-700', text: 'text-red-800' },
            { label: 'Zones', value: uniqueZones.length, accent: 'from-violet-600 to-indigo-700', text: 'text-violet-900' },
          ].map(({ label, value, accent, text }) => (
            <div
              key={label}
              className="card group relative overflow-hidden p-4 sm:p-5 border-ink-200/70 transition-all duration-300 hover:border-moss-200 hover:shadow-lift"
            >
              <div className={`absolute -right-6 -top-6 h-28 w-28 rounded-full bg-gradient-to-br ${accent} opacity-[0.14] blur-2xl`} aria-hidden />
              <p className="section-title relative">{label}</p>
              <p className={`font-display relative text-3xl sm:text-4xl font-bold tabular-nums mt-2 ${text}`}>{value}</p>
              <div className={`relative mt-3 h-1 w-12 rounded-full bg-gradient-to-r ${accent}`} aria-hidden />
            </div>
          ))}
        </div>

        {/* ── Map + Chart row ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/*
            `isolate` creates a new CSS stacking context for this card.
            Leaflet sets its own internal z-indices up to ~700 on map layers.
            Without isolation, those indices leak out and overlap the modal
            (z-[1000]) when it is opened. isolate keeps all Leaflet layers
            contained within this card's stacking context.
          */}
          <div className="card overflow-hidden isolate border-ink-200/80">
            <div className="px-5 pt-5 pb-3 border-b border-ink-100 bg-gradient-to-r from-parchment-deep to-moss-50/40">
              <div className="flex items-center gap-3">
                <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-moss-600 to-moss-400" aria-hidden />
                <div>
                  <h2 className="font-display text-base font-bold text-ink-950">Zone map</h2>
                  <p className="text-xs text-ink-500 mt-0.5 font-medium">Tap a marker to filter the rules table</p>
                </div>
              </div>
            </div>
            <div className="h-60">
              {aggregationLoading ? (
                <div className="flex h-full items-center justify-center text-sm text-ink-500">
                  Loading live zone summaries…
                </div>
              ) : (
                <ZoneMap
                  zoneSummaries={aggregationZones}
                  alerts={alerts}
                  selectedZone={selectedZone}
                  onZoneClick={handleZoneClick}
                />
              )}
            </div>
          </div>

          <div className="card p-5 border-ink-200/80">
            <div className="flex items-center gap-3 mb-4">
              <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-brand-500 to-moss-300" aria-hidden />
              <div>
                <h2 className="font-display text-base font-bold text-ink-950">Active by severity</h2>
                <p className="text-xs text-ink-500 font-medium">Stacked counts for live rules only</p>
              </div>
            </div>
            <div className="h-52">
              <SeverityChart thresholds={thresholds} />
            </div>
          </div>
        </div>

        {aggregationError && (
          <div className="rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm text-red-900">
            {aggregationError}
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8">
          <AggregationHistoryChart
            zone={chartZone}
            metric={chartMetric}
            points={historyData?.points ?? []}
            loading={historyLoading}
            error={historyError}
            zones={availableZones}
            metrics={[...KNOWN_METRICS]}
            selectedZone={chartZone}
            selectedMetric={chartMetric}
            onZoneChange={setChartZone}
            onMetricChange={setChartMetric}
          />

          <MetricGauge
            zones={availableZones}
            metrics={[...KNOWN_METRICS]}
            selectedZone={gaugeZone}
            selectedMetric={gaugeMetric}
            onZoneChange={setGaugeZone}
            onMetricChange={setGaugeMetric}
            zone={gaugeZoneSummary?.zone ?? null}
            metric={currentGaugeMetric?.metric ?? 'aqi'}
            value={currentGaugeMetric?.value ?? null}
            maxValue={currentGaugeMetric?.metric === 'temperature' ? 50 : currentGaugeMetric?.metric === 'humidity' ? 100 : currentGaugeMetric?.metric === 'noise' ? 140 : 200}
          />

          <PipelineHealthIndicator
            status={validationStatus}
            loading={validationLoading}
            error={validationError}
          />
        </div>

        {/* ── Table card ──────────────────────────────────────────────────────── */}
        <div className="card border-ink-200/80 overflow-hidden shadow-card-lg">
          <div className="px-4 sm:px-5 py-4 border-b border-ink-100 bg-gradient-to-r from-white via-parchment/50 to-moss-50/30 flex flex-wrap items-center gap-3 justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <span className="hidden sm:block h-9 w-1.5 rounded-full bg-gradient-to-b from-ink-800 to-moss-600 shrink-0" aria-hidden />
              <h2 className="font-display font-bold text-ink-950 truncate text-lg">
                Threshold rules
                <span className="ml-2 text-sm font-sans font-semibold text-ink-400 tabular-nums">{visible.length} shown</span>
              </h2>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Zone filter — changing this also moves the map highlight */}
              <select
                value={filter.zone}
                onChange={e => {
                  const zone = e.target.value;
                  setFilter(f => ({ ...f, zone: zone }));
                  setSelectedZone(zone || null);
                  if (zone) {
                    setChartZone(zone);
                    setGaugeZone(zone);
                  }
                }}
                className="input !py-1.5 !text-xs w-32"
              >
                <option value="">All zones</option>
                {uniqueZones.map(z => <option key={z} value={z}>{z}</option>)}
              </select>

              {/* Metric filter */}
              <select
                value={filter.metric}
                onChange={e => setFilter(f => ({ ...f, metric: e.target.value }))}
                className="input !py-1.5 !text-xs w-36"
              >
                <option value="">All metrics</option>
                {uniqueMetrics.map(m => <option key={m} value={m}>{m}</option>)}
              </select>

              {/* Status filter */}
              <select
                value={filter.status}
                onChange={e => setFilter(f => ({ ...f, status: e.target.value as Filter['status'] }))}
                className="input !py-1.5 !text-xs w-28"
              >
                <option value="all">All status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>

              {/* Show "Clear" only when at least one filter is active */}
              {(filter.zone || filter.metric || filter.status !== 'all') && (
                <button
                  onClick={() => { setFilter({ zone: '', metric: '', status: 'all' }); setSelectedZone(null); }}
                  className="btn-ghost !text-xs text-ink-500"
                >
                  Clear
                </button>
              )}

              {/* Manual refresh — useful when the evaluator has just fired */}
              <button
                type="button"
                onClick={() => {
                  void reload();
                  void loadAlerts();
                  void loadAggregationZones();
                  void loadValidationStatus();
                  void loadHistory();
                }}
                className="btn-ghost p-2 rounded-xl border border-transparent hover:border-ink-200"
                title="Refresh thresholds and alerts"
              >
                <svg className="w-4 h-4 text-ink-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>

              {/* Create button is admin-only; operators see the table but not this button */}
              {isAdmin && (
                <button onClick={openCreate} className="btn-primary">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                  New rule
                </button>
              )}
            </div>
          </div>

          {/* Loading spinner — shown until the first fetch resolves */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-ink-500">
              <svg className="animate-spin w-8 h-8 text-moss-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <p className="text-sm font-medium">Loading thresholds…</p>
            </div>
          )}

          {!loading && fetchError && (
            <div className="px-5 py-4 text-sm text-red-900 bg-red-50 border-t border-red-100 flex flex-wrap items-center gap-2">
              <span>{fetchError}</span>
              <button type="button" onClick={() => void reload()} className="font-semibold text-red-700 underline decoration-2 underline-offset-2 hover:text-red-900">Retry</button>
            </div>
          )}

          {/* Table is rendered only after a successful load */}
          {!loading && !fetchError && (
            <ThresholdTable
              thresholds={visible}
              isAdmin={isAdmin}
              onEdit={openEdit}
              onToggle={handleToggle}
              onDelete={handleDelete}
            />
          )}
        </div>
      </main>

      {/* Form modal — rendered as a portal sibling to main so the z-index stack
          is relative to the root rather than to the card's stacking context. */}
      {showForm && (
        <ThresholdFormModal
          initial={editTarget}
          onSave={handleSave}
          onClose={closeForm}
        />
      )}

      {currentViolation && (
        <ViolationAlertModal
          event={currentViolation}
          onDismiss={() => setViolationQueue(q => q.slice(1))}
          onResolved={() => void loadAlerts()}
          onViewAllAlerts={() => {
            setViolationQueue(q => q.slice(1));
            setBrowserInitialShowAll(true);
            setShowAlertsBrowser(true);
            void loadAlerts();
          }}
        />
      )}

      <AlertsBrowserModal
        isOpen={showAlertsBrowser}
        onClose={() => setShowAlertsBrowser(false)}
        alerts={alerts}
        loading={alertsLoading}
        error={alertsError}
        initialShowAll={browserInitialShowAll}
        onRefresh={() => void loadAlerts()}
      />
    </div>
  );
}
