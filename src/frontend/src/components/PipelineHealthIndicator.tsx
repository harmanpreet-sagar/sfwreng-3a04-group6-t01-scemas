/**
 * Validation pipeline health summary.
 */
import type { ValidationIssue, ValidationStatusResponse } from '../types';

interface Props {
  status: ValidationStatusResponse | null;
  issues: ValidationIssue[];
  zones: string[];
  selectedZone: string;
  selectedIssueStatus: 'all' | 'anomaly' | 'failed';
  onZoneChange: (zone: string) => void;
  onIssueStatusChange: (status: 'all' | 'anomaly' | 'failed') => void;
  loading: boolean;
  error: string | null;
}

export default function PipelineHealthIndicator({
  status,
  issues,
  zones,
  selectedZone,
  selectedIssueStatus,
  onZoneChange,
  onIssueStatusChange,
  loading,
  error,
}: Props) {
  const validCount = status?.valid ?? 0;
  const anomalyCount = status?.anomaly ?? 0;
  const failedCount = status?.failed ?? 0;
  const total = validCount + anomalyCount + failedCount;
  const lifetimeValid = validCount;
  const lifetimeAnomaly = anomalyCount;
  const lifetimeFailed = failedCount;

  return (
    <div className="card border-ink-200/80 overflow-hidden">
      <div className="px-5 pt-5 pb-4 border-b border-ink-100 bg-gradient-to-r from-white to-sky-50/50">
        <div className="flex items-center gap-3">
          <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-sky-600 to-cyan-400" aria-hidden />
          <div>
            <h2 className="font-display text-base font-bold text-ink-950">Pipeline health</h2>
            <p className="text-xs text-ink-500 font-medium">Validation events by zone with flagged reading drilldown</p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <select
            value={selectedZone}
            onChange={e => onZoneChange(e.target.value)}
            className="input !py-1.5 !text-xs w-36 bg-white/80"
          >
            <option value="">All zones</option>
            {zones.map(zone => (
              <option key={zone} value={zone}>{zone}</option>
            ))}
          </select>
          <select
            value={selectedIssueStatus}
            onChange={e => onIssueStatusChange(e.target.value as 'all' | 'anomaly' | 'failed')}
            className="input !py-1.5 !text-xs w-36 bg-white/80"
          >
            <option value="all">All flagged</option>
            <option value="anomaly">Anomalies</option>
            <option value="failed">Failed only</option>
          </select>
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
                <p className="mt-2 text-2xl font-bold text-emerald-900 tabular-nums">{validCount}</p>
                <p className="mt-1 text-[11px] text-emerald-700">Lifetime {lifetimeValid}</p>
              </div>
              <div className="rounded-xl bg-amber-50 px-3 py-3 ring-1 ring-amber-100">
                <p className="text-[11px] uppercase tracking-[0.2em] text-amber-700">Anomaly</p>
                <p className="mt-2 text-2xl font-bold text-amber-900 tabular-nums">{anomalyCount}</p>
                <p className="mt-1 text-[11px] text-amber-700">Lifetime {lifetimeAnomaly}</p>
              </div>
              <div className="rounded-xl bg-red-50 px-3 py-3 ring-1 ring-red-100">
                <p className="text-[11px] uppercase tracking-[0.2em] text-red-700">Failed</p>
                <p className="mt-2 text-2xl font-bold text-red-900 tabular-nums">{failedCount}</p>
                <p className="mt-1 text-[11px] text-red-700">Lifetime {lifetimeFailed}</p>
              </div>
            </div>
            <p className="mt-4 text-xs text-ink-500">Total checked: {total}</p>
            <div className="mt-4 rounded-2xl border border-ink-100 bg-white/80 p-3 min-h-[11rem]">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-500">
                  Anomaly / failed readings
                </p>
                <p className="text-[11px] text-ink-400">{issues.length} shown</p>
              </div>
              {issues.length === 0 ? (
                <p className="mt-4 text-sm text-ink-500">No recent anomaly or failed readings.</p>
              ) : (
                <div className="mt-3 space-y-2 max-h-44 overflow-y-auto pr-1">
                  {issues.map((issue, index) => {
                    const badgeTone = issue.status === 'failed'
                      ? 'bg-red-100 text-red-900 ring-red-200/80'
                      : 'bg-amber-100 text-amber-900 ring-amber-200/80';
                    return (
                      <div
                        key={`${issue.timestamp}-${issue.zone ?? 'unknown'}-${issue.metric ?? 'unknown'}-${index}`}
                        className="rounded-xl border border-ink-100 bg-parchment/55 px-3 py-2"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-ink-900">
                              {issue.zone ?? 'unknown zone'} · {issue.metric ?? 'unknown metric'}
                            </p>
                            <p className="mt-1 text-xs text-ink-500">
                              {new Date(issue.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <span className={`badge ring-1 ${badgeTone}`}>
                            {issue.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-ink-700">
                          {issue.value == null ? 'No numeric value available' : `Value ${issue.value.toFixed(2)}`}
                        </p>
                        <p className="mt-1 text-xs leading-relaxed text-ink-500">{issue.reason}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
