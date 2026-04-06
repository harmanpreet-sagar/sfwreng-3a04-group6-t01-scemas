/**
 * Validation pipeline health summary.
 */
import type { ValidationStatusResponse } from '../types';

interface Props {
  status: ValidationStatusResponse | null;
  loading: boolean;
  error: string | null;
}

export default function PipelineHealthIndicator({ status, loading, error }: Props) {
  const total = (status?.valid ?? 0) + (status?.failed ?? 0) + (status?.anomaly ?? 0);

  return (
    <div className="card border-ink-200/80 overflow-hidden">
      <div className="px-5 pt-5 pb-4 border-b border-ink-100 bg-gradient-to-r from-white to-sky-50/50">
        <div className="flex items-center gap-3">
          <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-sky-600 to-cyan-400" aria-hidden />
          <div>
            <h2 className="font-display text-base font-bold text-ink-950">Pipeline health</h2>
            <p className="text-xs text-ink-500 font-medium">Validation outcomes from the last 60 minutes</p>
          </div>
        </div>
      </div>

      <div className="p-4">
        {loading && <p className="text-sm text-ink-500">Loading validation status…</p>}
        {!loading && error && <p className="text-sm text-red-700">{error}</p>}
        {!loading && !error && status && (
          <>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-emerald-50 px-3 py-3 ring-1 ring-emerald-100">
                <p className="text-[11px] uppercase tracking-[0.2em] text-emerald-700">Valid</p>
                <p className="mt-2 text-2xl font-bold text-emerald-900 tabular-nums">{status.valid}</p>
              </div>
              <div className="rounded-xl bg-amber-50 px-3 py-3 ring-1 ring-amber-100">
                <p className="text-[11px] uppercase tracking-[0.2em] text-amber-700">Anomaly</p>
                <p className="mt-2 text-2xl font-bold text-amber-900 tabular-nums">{status.anomaly}</p>
              </div>
              <div className="rounded-xl bg-red-50 px-3 py-3 ring-1 ring-red-100">
                <p className="text-[11px] uppercase tracking-[0.2em] text-red-700">Failed</p>
                <p className="mt-2 text-2xl font-bold text-red-900 tabular-nums">{status.failed}</p>
              </div>
            </div>
            <p className="mt-4 text-xs text-ink-500">Total checked: {total}</p>
          </>
        )}
      </div>
    </div>
  );
}
