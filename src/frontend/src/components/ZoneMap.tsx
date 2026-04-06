/**
 * Live operator map showing one marker per zone with current metrics in the popup.
 */
import { useEffect } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet';
import type { AggregationZoneSummary, Alert, Severity } from '../types';
import { KNOWN_METRICS } from '../types';
import { CAMPUS_CENTER, ZONE_COORDS } from '../constants/zoneMap';
import '../map/leafletDefaultIcon';
import { formatMetricValue, metricLabel } from '../lib/metrics';

const SEVERITY_COLOUR: Record<'normal' | Severity, string> = {
  normal: '#14b8a6',
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#f59e0b',
  critical: '#ef4444',
};

interface ZoneInfo {
  zone: string;
  coords: [number, number];
  worstSeverity: 'normal' | Severity;
  metrics: Record<string, number | null>;
}

function buildZoneInfo(zoneSummaries: AggregationZoneSummary[], alerts: Alert[]): ZoneInfo[] {
  const summaryByZone = Object.fromEntries(zoneSummaries.map(z => [z.zone, z]));
  return Object.entries(ZONE_COORDS).map(([zone, coords]) => {
    const summary = summaryByZone[zone];
    const active = alerts.filter(a => a.zone === zone && a.status === 'active');
    const order: Severity[] = ['critical', 'high', 'medium', 'low'];
    const worstSeverity = order.find(s => active.some(a => a.severity === s)) ?? 'normal';
    const metrics = Object.fromEntries(
      KNOWN_METRICS.map(metric => [
        metric,
        summary?.metrics.find(m => m.metric === metric)?.value ?? null,
      ]),
    );
    return { zone, coords, worstSeverity, metrics };
  });
}

interface Props {
  zoneSummaries: AggregationZoneSummary[];
  alerts: Alert[];
  selectedZone: string | null;
  onZoneClick: (zone: string) => void;
}

export default function ZoneMap({ zoneSummaries, alerts, selectedZone, onZoneClick }: Props) {
  const zones = buildZoneInfo(zoneSummaries, alerts);

  useEffect(() => {
    // no-op: Leaflet asset setup happens at module load time
  }, []);

  return (
    <MapContainer
      center={CAMPUS_CENTER}
      zoom={14}
      style={{ height: '100%', width: '100%', borderRadius: '0.75rem' }}
      zoomControl
      scrollWheelZoom={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {zones.map(({ zone, coords, worstSeverity, metrics }) => {
        const color = SEVERITY_COLOUR[worstSeverity];
        const isSelected = selectedZone === zone;

        return (
          <CircleMarker
            key={zone}
            center={coords}
            radius={isSelected ? 28 : 22}
            pathOptions={{
              color: isSelected ? '#0f766e' : color,
              fillColor: color,
              fillOpacity: isSelected ? 0.88 : 0.7,
              weight: isSelected ? 3 : 2,
            }}
            eventHandlers={{ click: () => onZoneClick(zone === selectedZone ? '' : zone) }}
          >
            <Tooltip permanent direction="center" className="!bg-transparent !border-0 !shadow-none">
              <div className="text-center pointer-events-none select-none">
                <div className="text-[10px] font-bold text-white drop-shadow">{zone}</div>
              </div>
            </Tooltip>
            <Popup>
              <div className="min-w-[180px] space-y-2">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Zone</p>
                  <p className="font-bold text-slate-900">{zone}</p>
                </div>
                <p className="text-xs font-medium capitalize text-slate-600">
                  Current status: {worstSeverity === 'normal' ? 'normal' : worstSeverity}
                </p>
                <div className="space-y-1.5 pt-1">
                  {KNOWN_METRICS.map(metric => (
                    <div key={metric} className="flex items-center justify-between rounded-lg bg-slate-50 px-2.5 py-1.5">
                      <span className="text-xs font-medium text-slate-700">{metricLabel(metric)}</span>
                      <span className="text-xs font-mono font-semibold text-slate-900">
                        {formatMetricValue(metric, metrics[metric])}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
