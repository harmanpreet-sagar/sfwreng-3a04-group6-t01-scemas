/**
 * Public-facing status cards derived from /public/zones.
 */
import type { PublicZoneSummary } from '../api/publicZones';
import { KNOWN_METRICS, KNOWN_ZONES } from '../types';
import { getAqiLabel, getAqiTone, getMetricQualityLabel, getMetricQualityTone } from '../lib/aqi';
import { formatMetricValue, metricLabel } from '../lib/metrics';

interface Props {
  zones: PublicZoneSummary[] | null;
}

function metricValue(zone: PublicZoneSummary, metric: string): number | null {
  return zone.metrics.find(m => m.metric === metric)?.value ?? null;
}

export default function PublicZoneStatusCards({ zones }: Props) {
  const zoneRows = zones && zones.length > 0
    ? zones
    : KNOWN_ZONES.map(zone => ({
        zone,
        metrics: [],
        updated_at: '',
        status: 'normal' as const,
        active_alert_highest_severity: null,
      }));

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {zoneRows.map(zone => {
        const aqi = metricValue(zone, 'aqi');
        const aqiLabel = getAqiLabel(aqi);
        return (
          <div key={zone.zone} className="rounded-2xl border border-ink-200/80 bg-white p-5 shadow-card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="section-title">Zone</p>
                <h3 className="font-display mt-1 text-2xl font-bold text-ink-950">{zone.zone}</h3>
              </div>
              <span className={`badge ring-1 ${getAqiTone(aqi)}`}>{aqiLabel}</span>
            </div>

            <div className="mt-4 space-y-2">
              {KNOWN_METRICS.map(metric => {
                const value = metricValue(zone, metric);
                return (
                  <div key={metric} className="flex items-center justify-between rounded-xl bg-parchment/70 px-3 py-2">
                    <div>
                      <span className="text-sm font-medium text-ink-700">{metricLabel(metric)}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-ink-900 tabular-nums">
                        {formatMetricValue(metric, value)}
                      </p>
                      <span className={`badge ring-1 ${getMetricQualityTone(metric, value)}`}>
                        {getMetricQualityLabel(metric, value)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {(!zones || zones.length === 0) && (
              <p className="mt-4 text-xs text-ink-500">
                Live qualitative status will appear once public summaries are available.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
