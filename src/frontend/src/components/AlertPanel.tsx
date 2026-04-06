/**
 * Compact dashboard alert panel with acknowledge / resolve actions.
 */
import { useMemo, useState } from 'react';
import { acknowledgeAlert, resolveAlert } from '../api/alerts';
import type { Alert } from '../types';
import SeverityBadge from './SeverityBadge';

interface Props {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
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

export default function AlertPanel({ alerts, loading, error, onRefresh }: Props) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const visible = useMemo(
    () => [...alerts]
      .filter(a => a.status !== 'resolved')
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5),
    [alerts],
  );

  async function run(id: number, action: (id: number) => Promise<Alert>) {
    setLocalError(null);
    setBusyId(id);
    try {
      await action(id);
      onRefresh();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: { message?: string } | string } } })?.response?.data?.detail;
      setLocalError(typeof detail === 'string' ? detail : (detail as { message?: string })?.message ?? 'Request failed.');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="card border-ink-200/80 overflow-hidden">
      <div className="px-5 pt-5 pb-4 border-b border-ink-100 bg-gradient-to-r from-white to-red-50/40">
        <div className="flex items-center gap-3">
          <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-red-600 to-orange-400" aria-hidden />
          <div>
            <h2 className="font-display text-base font-bold text-ink-950">Alert panel</h2>
            <p className="text-xs text-ink-500 font-medium">Latest active or acknowledged issues</p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {loading && <p className="text-sm text-ink-500">Loading alerts…</p>}
        {!loading && error && <p className="text-sm text-red-700">{error}</p>}
        {!loading && !error && localError && <p className="text-sm text-red-700">{localError}</p>}
        {!loading && !error && visible.length === 0 && (
          <div className="rounded-xl border border-dashed border-ink-200 bg-parchment/50 px-4 py-8 text-center">
            <p className="text-sm font-medium text-ink-700">No active alerts</p>
            <p className="text-xs text-ink-500 mt-1">The dashboard is currently quiet.</p>
          </div>
        )}

        {!loading && !error && visible.map(alert => (
          <div key={alert.id} className="rounded-xl border border-ink-200/80 bg-white px-4 py-3 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-ink-950">{alert.zone}</span>
                  <span className="text-ink-400">·</span>
                  <span className="text-sm font-medium text-ink-700">{alert.metric}</span>
                  <SeverityBadge severity={alert.severity} />
                  <span className="badge ring-1 capitalize bg-slate-100 text-slate-800 ring-slate-200/80">
                    {alert.status}
                  </span>
                </div>
                <p className="mt-2 text-sm text-ink-700 leading-snug">{alert.message}</p>
                <p className="mt-1 text-xs text-ink-500">{formatWhen(alert.created_at)}</p>
              </div>
              <div className="flex shrink-0 flex-col gap-2">
                {alert.status === 'active' && (
                  <button
                    type="button"
                    className="btn-secondary !py-1.5 !text-xs"
                    disabled={busyId === alert.id}
                    onClick={() => void run(alert.id, acknowledgeAlert)}
                  >
                    {busyId === alert.id ? '…' : 'Acknowledge'}
                  </button>
                )}
                {(alert.status === 'active' || alert.status === 'acknowledged') && (
                  <button
                    type="button"
                    className="btn-primary !py-1.5 !text-xs"
                    disabled={busyId === alert.id}
                    onClick={() => void run(alert.id, resolveAlert)}
                  >
                    {busyId === alert.id ? '…' : 'Resolve'}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
