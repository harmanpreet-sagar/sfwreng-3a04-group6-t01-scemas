/**
 * AQI helpers shared by public cards and dashboard summaries.
 */

export function getAqiLabel(value: number | null | undefined): 'Good' | 'Moderate' | 'Poor' | 'Unknown' {
  if (value == null || Number.isNaN(value)) return 'Unknown';
  if (value <= 50) return 'Good';
  if (value <= 100) return 'Moderate';
  return 'Poor';
}

export function getAqiTone(value: number | null | undefined): string {
  const label = getAqiLabel(value);
  if (label === 'Good') return 'bg-emerald-100 text-emerald-900 ring-emerald-200/80';
  if (label === 'Moderate') return 'bg-amber-100 text-amber-900 ring-amber-200/80';
  if (label === 'Poor') return 'bg-red-100 text-red-900 ring-red-200/80';
  return 'bg-slate-100 text-slate-700 ring-slate-200/80';
}

export function getMetricQualityLabel(
  metric: string,
  value: number | null | undefined,
): 'Good' | 'Average' | 'Poor' | 'Unknown' {
  if (value == null || Number.isNaN(value)) return 'Unknown';

  if (metric === 'aqi') {
    if (value <= 50) return 'Good';
    if (value <= 100) return 'Average';
    return 'Poor';
  }

  if (metric === 'temperature') {
    if (value >= 18 && value <= 25) return 'Good';
    if ((value >= 10 && value < 18) || (value > 25 && value <= 30)) return 'Average';
    return 'Poor';
  }

  if (metric === 'humidity') {
    if (value >= 30 && value <= 60) return 'Good';
    if ((value >= 20 && value < 30) || (value > 60 && value <= 70)) return 'Average';
    return 'Poor';
  }

  if (metric === 'noise') {
    if (value <= 55) return 'Good';
    if (value <= 75) return 'Average';
    return 'Poor';
  }

  return 'Unknown';
}

export function getMetricQualityTone(metric: string, value: number | null | undefined): string {
  const label = getMetricQualityLabel(metric, value);
  if (label === 'Good') return 'bg-emerald-100 text-emerald-900 ring-emerald-200/80';
  if (label === 'Average') return 'bg-amber-100 text-amber-900 ring-amber-200/80';
  if (label === 'Poor') return 'bg-red-100 text-red-900 ring-red-200/80';
  return 'bg-slate-100 text-slate-700 ring-slate-200/80';
}

export function metricQualityScore(metric: string, value: number | null | undefined): number | null {
  const label = getMetricQualityLabel(metric, value);
  if (label === 'Good') return 2;
  if (label === 'Average') return 1;
  if (label === 'Poor') return 0;
  return null;
}

export function averageMetricQualityScore(
  metrics: Array<{ metric: string; value: number | null | undefined }>,
): number | null {
  const scores = metrics
    .map(item => metricQualityScore(item.metric, item.value))
    .filter((value): value is number => value != null);
  if (scores.length === 0) return null;
  return scores.reduce((sum, value) => sum + value, 0) / scores.length;
}

export function averageMetricQualityTone(score: number | null | undefined): string {
  if (score == null) return '#94a3b8';
  if (score >= 1.5) return '#14b8a6';
  if (score >= 0.75) return '#f59e0b';
  return '#ef4444';
}
