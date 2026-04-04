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
import { useAuth } from '../context/AuthContext';
import type { Threshold, ThresholdCreate } from '../types';
import ThresholdTable from '../components/ThresholdTable';
import ThresholdFormModal from '../components/ThresholdFormModal';
import SeverityChart from '../components/SeverityChart';
import ZoneMap from '../components/ZoneMap';

type Filter = { zone: string; metric: string; status: 'all' | 'active' | 'inactive' };

export default function ThresholdsPage() {
  const { account, isAdmin, signOut } = useAuth();
  const navigate = useNavigate();

  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

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
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ── Top nav ─────────────────────────────────────────────────────────── */}
      <header className="bg-slate-900 text-white shadow-md">
        <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <span className="font-semibold tracking-tight text-lg">SCEMAS</span>
            <span className="hidden sm:block text-slate-400 text-sm ml-2">Threshold Management</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden sm:block text-sm text-slate-300">
              {account?.name}
              {/* Clearance badge colour distinguishes admin from operator at a glance */}
              <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full font-medium
                ${isAdmin ? 'bg-blue-700 text-blue-100' : 'bg-slate-700 text-slate-300'}`}>
                {account?.clearance}
              </span>
            </span>
            <button
              onClick={() => { signOut(); navigate('/login', { replace: true }); }}
              className="btn-ghost text-slate-300 hover:text-white hover:bg-slate-700 text-sm"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-screen-xl mx-auto w-full px-6 py-6 space-y-6">

        {/* ── OPERATOR read-only banner ───────────────────────────────────────
            Shown proactively so operators understand why they cannot see the
            "New rule" button or toggle switches before they go looking for them. */}
        {!isAdmin && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 flex items-center gap-3 text-sm text-amber-800">
            <svg className="w-5 h-5 text-amber-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
            <span>You are logged in as <strong>OPERATOR</strong>. You can view thresholds but cannot create, edit, or delete them.</span>
          </div>
        )}

        {/* ── Stats row ──────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Rules',    value: thresholds.length, colour: 'text-blue-600',  bg: 'bg-blue-50'  },
            { label: 'Active',         value: totalActive,        colour: 'text-green-600', bg: 'bg-green-50' },
            { label: 'Critical Rules', value: totalCritical,      colour: 'text-red-600',   bg: 'bg-red-50'   },
            { label: 'Zones Covered',  value: uniqueZones.length, colour: 'text-purple-600',bg: 'bg-purple-50'},
          ].map(({ label, value, colour, bg }) => (
            <div key={label} className={`card p-4 ${bg}`}>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
              <p className={`text-3xl font-bold mt-1 ${colour}`}>{value}</p>
            </div>
          ))}
        </div>

        {/* ── Map + Chart row ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/*
            `isolate` creates a new CSS stacking context for this card.
            Leaflet sets its own internal z-indices up to ~700 on map layers.
            Without isolation, those indices leak out and overlap the modal
            (z-[1000]) when it is opened. isolate keeps all Leaflet layers
            contained within this card's stacking context.
          */}
          <div className="card overflow-hidden isolate">
            <div className="px-4 pt-4 pb-2">
              <h2 className="text-sm font-semibold text-gray-700">Zone Map</h2>
              <p className="text-xs text-gray-400 mt-0.5">Click a zone to filter the table</p>
            </div>
            <div className="h-60">
              <ZoneMap
                thresholds={thresholds}
                selectedZone={selectedZone}
                onZoneClick={handleZoneClick}
              />
            </div>
          </div>

          <div className="card p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-1">Active Thresholds by Severity</h2>
            <p className="text-xs text-gray-400 mb-3">Stacked count per metric</p>
            <div className="h-52">
              <SeverityChart thresholds={thresholds} />
            </div>
          </div>
        </div>

        {/* ── Table card ──────────────────────────────────────────────────────── */}
        <div className="card">
          {/* Card header with filter controls and (admin-only) create button */}
          <div className="px-4 py-3 border-b border-gray-100 flex flex-wrap items-center gap-3 justify-between">
            <h2 className="font-semibold text-gray-800">
              Threshold Rules
              {/* Show filtered count so users know when a filter is narrowing the view */}
              <span className="ml-2 text-sm font-normal text-gray-400">{visible.length} shown</span>
            </h2>

            <div className="flex flex-wrap items-center gap-2">
              {/* Zone filter — changing this also moves the map highlight */}
              <select
                value={filter.zone}
                onChange={e => { setFilter(f => ({ ...f, zone: e.target.value })); setSelectedZone(e.target.value || null); }}
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
                  className="btn-ghost !text-xs text-gray-400"
                >
                  Clear
                </button>
              )}

              {/* Manual refresh — useful when the evaluator has just fired */}
              <button
                onClick={() => void reload()}
                className="btn-ghost p-1.5"
                title="Refresh"
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
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
            <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
              <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Loading thresholds…
            </div>
          )}

          {/* Fetch error — shown with a retry link rather than an error boundary */}
          {!loading && fetchError && (
            <div className="px-4 py-4 text-sm text-red-600 bg-red-50 border-t border-red-100">
              {fetchError}
              <button onClick={() => void reload()} className="ml-2 underline">Retry</button>
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
    </div>
  );
}
