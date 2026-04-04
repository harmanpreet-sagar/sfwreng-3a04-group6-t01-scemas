/**
 * SeverityChart — stacked bar chart showing active threshold counts by metric
 * and severity, built with Recharts.
 *
 * Why stacked bars:
 *  A single bar per metric would show only the total count, hiding whether
 *  those rules are mostly low-risk or mostly critical. Stacking by severity
 *  lets operators see the risk composition at a glance — a metric with many
 *  critical segments needs attention even if its total count is low.
 *
 * Data pipeline:
 *  buildChartData groups ACTIVE thresholds (is_active === true) by metric,
 *  then counts how many rules exist at each severity level. Inactive thresholds
 *  are excluded because they do not affect the evaluator and should not inflate
 *  the visual weight of a metric.
 *
 * Colour consistency:
 *  SEVERITY_COLOUR values here intentionally match those in ZoneMap.tsx and
 *  SeverityBadge.tsx. If the severity palette changes, update all three files.
 *
 * Recharts note:
 *  stackId="a" on every Bar tells Recharts to group them into a single stack
 *  per x-axis value. Using different stackId values would produce grouped
 *  (side-by-side) bars instead.
 *
 *  The top-most bar (critical) gets a corner radius of [3,3,0,0] so the whole
 *  stack has rounded top corners. Other bars use [0,0,0,0] to avoid gaps
 *  between stacked segments.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell,
} from 'recharts';
import type { Severity, Threshold } from '../types';

const SEVERITY_COLOUR: Record<Severity, string> = {
  low:      '#22c55e',
  medium:   '#eab308',
  high:     '#f97316',
  critical: '#ef4444',
};

// Fixed order ensures the stack always renders low → critical bottom to top,
// making it easy to visually compare severity distribution across metrics.
const SEVERITIES: Severity[] = ['low', 'medium', 'high', 'critical'];

interface ChartRow {
  metric: string;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

/**
 * Transform the flat threshold list into one row per metric with per-severity counts.
 * Only active thresholds are counted — inactive rules do not affect the evaluator.
 */
function buildChartData(thresholds: Threshold[]): ChartRow[] {
  const metrics = [...new Set(thresholds.map(t => t.metric))].sort();
  return metrics.map(metric => {
    const row: ChartRow = { metric, low: 0, medium: 0, high: 0, critical: 0 };
    for (const t of thresholds.filter(t2 => t2.metric === metric && t2.is_active)) {
      row[t.severity]++;
    }
    return row;
  });
}

export default function SeverityChart({ thresholds }: { thresholds: Threshold[] }) {
  const data = buildChartData(thresholds);

  // Empty state for when no thresholds exist or all are inactive
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        No active thresholds to display
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="metric"
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={false}
          className="capitalize"
        />
        {/* allowDecimals=false because threshold counts are always whole numbers */}
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
          cursor={{ fill: '#f8fafc' }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
        />
        {SEVERITIES.map(s => (
          <Bar
            key={s}
            dataKey={s}
            name={s}
            stackId="a"
            // Only the top segment gets rounded corners to avoid visual gaps between segments
            radius={s === 'critical' ? [3, 3, 0, 0] : [0, 0, 0, 0]}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={SEVERITY_COLOUR[s]} />
            ))}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
