/**
 * Radial gauge for one live aggregate value.
 */
import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';

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

  return (
    <div className="card border-ink-200/80 overflow-hidden">
      <div className="px-5 pt-5 pb-4 border-b border-ink-100 bg-gradient-to-r from-white to-moss-50/40">
        <div className="flex items-center gap-3">
          <span className="h-9 w-1.5 rounded-full bg-gradient-to-b from-moss-600 to-brand-400" aria-hidden />
          <div>
            <h2 className="font-display text-base font-bold text-ink-950">Current metric</h2>
            <p className="text-xs text-ink-500 font-medium">
              {zone ? `${zone} · ${metric}` : `No zone selected · ${metric}`}
            </p>
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
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              data={data}
              innerRadius="68%"
              outerRadius="100%"
              startAngle={180}
              endAngle={0}
              barSize={18}
            >
              <PolarAngleAxis type="number" domain={[0, maxValue]} tick={false} axisLine={false} />
              <RadialBar dataKey="value" background={{ fill: '#e5e7eb' }} cornerRadius={10} />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        <div className="-mt-10 text-center">
          <p className="font-display text-4xl font-bold text-ink-950">
            {value == null ? '—' : value.toFixed(1)}
          </p>
          <p className="mt-1 text-xs uppercase tracking-[0.2em] text-ink-500">{metric}</p>
        </div>
      </div>
    </div>
  );
}
