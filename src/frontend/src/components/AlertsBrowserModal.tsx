/**
 * Modal listing alerts — default active only; toggle shows full history.
 */
import { useEffect, useMemo, useState } from 'react';
import type { Alert, AlertStatus } from '../types';
import SeverityBadge from './SeverityBadge';
import { resolveAlert } from '../api/alerts';

const STATUS_STYLE: Record<AlertStatus, string> = {
  active: 'bg-red-100 text-red-900 ring-red-200/80',
  acknowledged: 'bg-moss-100 text-moss-900 ring-moss-200/80',
  resolved: 'bg-slate-200 text-slate-800 ring-slate-300/80',
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  /** When true, start with history toggle on */
  initialShowAll?: boolean;
  onRefresh: () => void;
}

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export default function AlertsBrowserModal({
  isOpen,
  onClose,
  alerts,
  loading,
  error,
  initialShowAll = false,
  onRefresh,
}: Props) {
  const [showAll, setShowAll] = useState(initialShowAll);
  const [actionId, setActionId] = useState<number | null>(null);
  const [localErr, setLocalErr] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) setShowAll(initialShowAll);
  }, [isOpen, initialShowAll]);

  const visible = useMemo(() => {
    const sorted = [...alerts].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
    if (showAll) return sorted;
    return sorted.filter(a => a.status === 'active');
  }, [alerts, showAll]);

  const activeCount = alerts.filter(a => a.status === 'active').length;

  async function run(id: number, fn: (n: number) => Promise<Alert>) {
    setLocalErr(null);
    setActionId(id);
    try {
      await fn(id);
      onRefresh();
    } catch (e: unknown) {
      const d = (e as { response?: { data?: { detail?: { message?: string } | string } } })?.response
        ?.data?.detail;
      const text =
        typeof d === 'string' ? d : (d as { message?: string })?.message ?? 'Request failed.';
      setLocalErr(text);
    } finally {
      setActionId(null);
    }
  }

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[1010] flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="alerts-browser-title"
    >
      <button type="button" className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" aria-label="Close" onClick={onClose} />
      <div className="relative flex max-h-[min(90vh,720px)] w-full max-w-3xl flex-col rounded-2xl border border-slate-200/90 bg-white shadow-2xl ring-1 ring-slate-900/[0.06] overflow-hidden">
        <div className="shrink-0 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-brand-50/40 px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-teal-600 text-white shadow-md shadow-teal-900/20">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
                  />
                </svg>
              </div>
              <div>
                <h2 id="alerts-browser-title" className="text-lg font-bold text-slate-900 tracking-tight">
                  Alerts
                </h2>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  {activeCount} active
                  {!showAll && alerts.length > activeCount && (
                    <span className="text-slate-400"> · {alerts.length} total in system</span>
                  )}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="Close dialog"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <label className="mt-4 flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200/80 bg-white/80 px-3 py-2.5 shadow-sm">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              checked={showAll}
              onChange={e => setShowAll(e.target.checked)}
            />
            <span className="text-sm text-slate-700">
              <span className="font-semibold text-slate-900">View all alerts</span>
              <span className="block text-xs text-slate-500 font-normal">
                Include acknowledged and resolved (history)
              </span>
            </span>
          </label>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-2 sm:px-3 py-3">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-2 text-slate-500">
              <svg className="animate-spin w-8 h-8 text-brand-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <p className="text-sm font-medium">Loading alerts…</p>
            </div>
          )}

          {!loading && error && (
            <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
          )}

          {!loading && !error && localErr && (
            <div className="mb-3 rounded-xl border border-red-100 bg-red-50 px-4 py-2 text-sm text-red-800">
              {localErr}
            </div>
          )}

          {!loading && !error && visible.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/80 px-6 py-12 text-center">
              <p className="text-slate-600 font-medium">No alerts to show</p>
              <p className="text-sm text-slate-500 mt-1">
                {showAll ? 'The system has no alert records yet.' : 'There are no active alerts right now.'}
              </p>
            </div>
          )}

          {!loading && !error && visible.length > 0 && (
            <ul className="space-y-3">
              {visible.map(a => (
                <li
                  key={a.id}
                  className="rounded-xl border border-slate-200/90 bg-white px-4 py-3 shadow-sm ring-1 ring-slate-900/[0.02]"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-slate-900">{a.zone}</span>
                        <span className="text-slate-400">·</span>
                        <span className="font-semibold text-slate-700">{a.metric}</span>
                        <SeverityBadge severity={a.severity} />
                        <span className={`badge ring-1 capitalize ${STATUS_STYLE[a.status]}`}>{a.status}</span>
                      </div>
                      <p className="text-sm text-slate-600 leading-snug">{a.message}</p>
                      <p className="text-xs text-slate-400 font-medium">
                        {formatWhen(a.created_at)}
                        {a.observed_value != null && a.threshold_value != null && (
                          <span className="text-slate-500">
                            {' '}
                            · observed <span className="font-mono">{a.observed_value}</span> vs threshold{' '}
                            <span className="font-mono">{a.threshold_value}</span>
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 shrink-0">
                      {(a.status === 'active' || a.status === 'acknowledged') && (
                        <button
                          type="button"
                          disabled={actionId === a.id}
                          className="btn-primary !py-1.5 !text-xs"
                          onClick={() => void run(a.id, resolveAlert)}
                          title="Marks the alert resolved (closes it from active or acknowledged)"
                        >
                          {actionId === a.id ? '…' : 'Resolve'}
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
