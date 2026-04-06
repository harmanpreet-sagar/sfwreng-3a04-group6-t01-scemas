/**
 * Adjustable aggregation history chart for one zone + metric.
 */
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { AggregationHistoryPoint } from '../types';

interface Props {
  zone: string;
  metric: string;
  points: AggregationHistoryPoint[];
  loading: boolean;
  error: string | null;
  zones: string[];
  metrics: string[];
  selectedZone: string;
  selectedMetric: string;
  onZoneChange: (zone: string) => void;
  onMetricChange: (metric: string) => void;
}

function labelForTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  } catch {
    return iso;
  }
}

export default function AggregationHistoryChart({
  zone,
  metric,
  points,
  loading,
  error,
  zones,
  metrics,
  selectedZone,
  selectedMetric,
  onZoneChange,
  onMetricChange,
}: Props) {
  const data = points.map(point => ({
    label: labelForTime(point.window_end),
    value: point.value,
  }));

  return (
    <div className="card border-ink-200/80 overflow-hidden">
      <div className="px-5 pt-5 pb-4 border-b border-ink-100 bg-gradient-to-r from-white to-orange-50/40">
        <div className="flex items-center gap-3">
          <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-orange-500 to-red-400" aria-hidden />
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-base font-bold text-ink-950">Metric history</h2>
            <p className="text-xs text-ink-500 font-medium">{zone} · {metric} · last {points.length} points</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <select
            value={selectedZone}
            onChange={e => onZoneChange(e.target.value)}
            className="input !py-1.5 !text-xs w-32"
          >
            {zones.map(option => <option key={option} value={option}>{option}</option>)}
          </select>
          <select
            value={selectedMetric}
            onChange={e => onMetricChange(e.target.value)}
            className="input !py-1.5 !text-xs w-36"
          >
            {metrics.map(option => <option key={option} value={option}>{option}</option>)}
          </select>
        </div>
      </div>

      <div className="p-4">
        {loading && <p className="text-sm text-ink-500">Loading history…</p>}
        {!loading && error && <p className="text-sm text-red-700">{error}</p>}
        {!loading && !error && data.length === 0 && (
          <div className="rounded-xl border border-dashed border-ink-200 bg-parchment/50 px-4 py-10 text-center">
            <p className="text-sm font-medium text-ink-700">No chart data yet</p>
            <p className="text-xs text-ink-500 mt-1">Aggregation history will appear after the worker writes buckets.</p>
          </div>
        )}
        {!loading && !error && data.length > 0 && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ece8de" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#dc2626"
                  strokeWidth={3}
                  dot={{ r: 3, fill: '#dc2626' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
