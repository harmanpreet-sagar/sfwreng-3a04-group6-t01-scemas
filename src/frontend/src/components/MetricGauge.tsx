/**
 * Radial gauge for one live aggregate value.
 */
import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';
import { formatMetricValue, metricLabel, metricUnit } from '../lib/metrics';

interface Props {
  zones: string[];
  metrics: string[];
  selectedZone: string;
  selectedMetric: string;
  onZoneChange: (zone: string) => void;
  onMetricChange: (metric: string) => void;
  zone: string | null;
  metric: string;
  value: number | null;
  maxValue?: number;
}

export default function MetricGauge({
  zones,
  metrics,
  selectedZone,
  selectedMetric,
  onZoneChange,
  onMetricChange,
  zone,
  metric,
  value,
  maxValue = 200,
}: Props) {
  const clamped = Math.max(0, Math.min(value ?? 0, maxValue));
  const data = [{ name: metric, value: clamped, fill: clamped > maxValue * 0.66 ? '#ef4444' : clamped > maxValue * 0.33 ? '#f59e0b' : '#14b8a6' }];
  const unit = metricUnit(metric);
  const band = value == null
    ? 'No data'
    : clamped > maxValue * 0.66
      ? 'High'
      : clamped > maxValue * 0.33
        ? 'Elevated'
        : 'Stable';

  return (
    <div className="card border-ink-200/80 overflow-hidden">
      <div className="px-5 pt-5 pb-4 border-b border-ink-100 bg-gradient-to-r from-white to-moss-50/40">
        <div className="flex items-center gap-3">
          <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-moss-600 to-brand-400" aria-hidden />
          <div>
            <h2 className="font-display text-base font-bold text-ink-950">Current metric</h2>
            <p className="text-xs text-ink-500 font-medium">
              {zone ? `${zone} · ${metricLabel(metric)}` : `No zone selected · ${metricLabel(metric)}`}
            </p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <select
            value={selectedZone}
            onChange={e => onZoneChange(e.target.value)}
            className="input !py-2 !text-xs !font-medium rounded-xl bg-white/90 border-ink-200"
          >
            {zones.map(option => <option key={option} value={option}>{option}</option>)}
          </select>
          <select
            value={selectedMetric}
            onChange={e => onMetricChange(e.target.value)}
            className="input !py-2 !text-xs !font-medium rounded-xl bg-white/90 border-ink-200"
          >
            {metrics.map(option => <option key={option} value={option}>{option}</option>)}
          </select>
        </div>
      </div>

      <div className="p-5">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              data={data}
              innerRadius="64%"
              outerRadius="104%"
              startAngle={180}
              endAngle={0}
              barSize={22}
            >
              <PolarAngleAxis type="number" domain={[0, maxValue]} tick={false} axisLine={false} />
              <RadialBar dataKey="value" background={{ fill: '#e5e7eb' }} cornerRadius={10} />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        <div className="-mt-16 text-center">
          <p className="font-display text-5xl font-bold text-ink-950">
            {value == null ? '—' : value.toFixed(1)}
          </p>
          <p className="mt-1 text-xs uppercase tracking-[0.2em] text-ink-500">{unit || metricLabel(metric)}</p>
          <div className="mt-5 grid grid-cols-2 gap-3 text-left">
            <div className="rounded-xl bg-parchment/70 px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-ink-500">Current</p>
              <p className="mt-1 text-sm font-semibold text-ink-900">{formatMetricValue(metric, value)}</p>
            </div>
            <div className="rounded-xl bg-parchment/70 px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-ink-500">Band</p>
              <p className="mt-1 text-sm font-semibold text-ink-900">{band}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
