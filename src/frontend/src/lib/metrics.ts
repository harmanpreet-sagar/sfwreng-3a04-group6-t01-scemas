/**
 * Shared metric display helpers for public and operational dashboards.
 */

export function metricUnit(metric: string): string {
  if (metric === 'aqi') return 'AQI';
  if (metric === 'temperature') return '°C';
  if (metric === 'humidity') return '%';
  if (metric === 'noise') return 'dB';
  return '';
}

export function metricLabel(metric: string): string {
  if (metric === 'aqi') return 'AQI';
  if (metric === 'temperature') return 'Temperature';
  if (metric === 'humidity') return 'Humidity';
  if (metric === 'noise') return 'Noise';
  return metric;
}

export function formatMetricValue(metric: string, value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  const unit = metricUnit(metric);
  const formatted = value.toFixed(1);
  return unit ? `${formatted} ${unit}` : formatted;
}
