/**
 * Full-screen emphasis modal when a new threshold violation is pushed over SSE.
 */
import { useState } from 'react';
import type { SseAlertEvent } from '../types';
import SeverityBadge from './SeverityBadge';
import { resolveAlert } from '../api/alerts';

interface Props {
  event: SseAlertEvent;
  onDismiss: () => void;
  /** After a successful resolve, parent refetches lists / updates badge */
  onResolved: () => void;
  /** Opens the full alerts browser (parent should close this modal) */
  onViewAllAlerts: () => void;
}

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export default function ViolationAlertModal({
  event,
  onDismiss,
  onResolved,
  onViewAllAlerts,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  /** Backend allows resolve from active or acknowledged in one step (no separate ack required). */
  const canResolve = event.status === 'active' || event.status === 'acknowledged';

  async function handleResolve() {
    setErr(null);
    setBusy(true);
    try {
      await resolveAlert(event.id);
      onResolved();
      onDismiss();
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: { message?: string } | string } } })?.response?.data
          ?.detail;
      const text =
        typeof msg === 'string' ? msg : (msg as { message?: string })?.message ?? 'Could not resolve.';
      setErr(text);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[1020] flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="violation-alert-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm"
        aria-label="Close"
        onClick={onDismiss}
      />
      <div className="relative w-full max-w-lg rounded-2xl border border-red-200/80 bg-white shadow-2xl shadow-red-900/10 ring-1 ring-red-500/20 overflow-hidden">
        <div className="bg-gradient-to-r from-red-600 via-rose-600 to-orange-500 px-5 py-4 text-white">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/20 ring-1 ring-white/30">
                <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                  />
                </svg>
              </div>
              <div className="min-w-0">
                <p id="violation-alert-title" className="text-lg font-bold leading-tight">
                  Threshold violated
                </p>
                <p className="text-sm text-white/90 mt-0.5">New alert · {formatWhen(event.created_at)}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-slate-500">Severity</span>
            <SeverityBadge severity={event.severity} />
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Zone</dt>
              <dd className="font-semibold text-slate-900 mt-0.5">{event.zone}</dd>
            </div>
            <div className="rounded-xl bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Metric</dt>
              <dd className="font-semibold text-slate-900 mt-0.5">{event.metric}</dd>
            </div>
            <div className="col-span-2 rounded-xl bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Status</dt>
              <dd className="font-semibold text-slate-900 mt-0.5 capitalize">{event.status}</dd>
            </div>
            <div className="col-span-2 rounded-xl bg-moss-50/90 px-3 py-2 ring-1 ring-moss-100">
              <dt className="text-xs font-bold uppercase tracking-wide text-moss-800/90">Message</dt>
              <dd className="text-slate-800 mt-1 leading-relaxed">{event.message}</dd>
            </div>
            <div className="rounded-xl bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Observed</dt>
              <dd className="font-mono font-semibold text-slate-900 mt-0.5">
                {event.observed_value != null ? event.observed_value : '—'}
              </dd>
            </div>
            <div className="rounded-xl bg-slate-50 px-3 py-2 ring-1 ring-slate-100">
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Threshold</dt>
              <dd className="font-mono font-semibold text-slate-900 mt-0.5">
                {event.threshold_value != null ? event.threshold_value : '—'}
              </dd>
            </div>
          </dl>

          {err && (
            <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{err}</p>
          )}

          <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-1">
            <button type="button" onClick={onDismiss} className="btn-secondary w-full sm:w-auto">
              Dismiss
            </button>
            <button type="button" onClick={onViewAllAlerts} className="btn-secondary w-full sm:w-auto">
              View all alerts
            </button>
            {canResolve && (
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleResolve()}
                className="btn-primary w-full sm:w-auto"
              >
                {busy ? 'Resolving…' : 'Resolve alert'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
