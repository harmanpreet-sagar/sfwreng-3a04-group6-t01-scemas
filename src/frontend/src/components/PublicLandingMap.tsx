/**
 * Public-facing zone map for the marketing landing page.
 * Uses /public/zones data when VITE_PUBLIC_DEMO_API_KEY is set; otherwise shows coverage only.
 */
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { CAMPUS_CENTER, ZONE_COORDS } from '../constants/zoneMap';
import '../map/leafletDefaultIcon';
import type { PublicZoneSummary } from '../api/publicZones';
import { staticZoneIds } from '../api/publicZones';
import { KNOWN_METRICS } from '../types';
import {
  averageMetricQualityScore,
  averageMetricQualityTone,
  getMetricQualityLabel,
  getMetricQualityTone,
} from '../lib/aqi';
import { formatMetricValue, metricLabel } from '../lib/metrics';

interface Props {
  /** Live summaries from public API, or null to show static coverage */
  zones: PublicZoneSummary[] | null;
}

export default function PublicLandingMap({ zones }: Props) {
  const byZone = zones ? Object.fromEntries(zones.map(z => [z.zone, z])) : {};
  const ids = zones && zones.length > 0 ? zones.map(z => z.zone) : staticZoneIds();

  return (
    <MapContainer
      center={CAMPUS_CENTER}
      zoom={13}
      className="h-[min(420px,55vh)] w-full rounded-2xl z-0"
      scrollWheelZoom={false}
      zoomControl
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {ids.map(zoneId => {
        const coords = ZONE_COORDS[zoneId];
        if (!coords) return null;
        const row = byZone[zoneId];
        const averageScore = averageMetricQualityScore(
          KNOWN_METRICS.map(metric => ({
            metric,
            value: row?.metrics.find(m => m.metric === metric)?.value ?? null,
          })),
        );
        const fill = averageMetricQualityTone(averageScore);
        const subtitle = averageScore == null
          ? 'Awaiting live summary'
          : averageScore >= 1.5
            ? 'Mostly good'
            : averageScore >= 0.75
              ? 'Mixed / average'
              : 'Mostly poor';

        return (
          <CircleMarker
            key={zoneId}
            center={coords}
            radius={26}
            pathOptions={{
              color: '#0f766e',
              fillColor: fill,
              fillOpacity: 0.72,
              weight: 2,
            }}
          >
            <Tooltip direction="top" offset={[0, -8]} opacity={1}>
              <div className="text-xs font-semibold text-slate-800">{zoneId}</div>
              <div className="text-[11px] text-slate-600">{subtitle}</div>
            </Tooltip>
            <Popup>
              <div className="min-w-[180px] space-y-2">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Zone</p>
                  <p className="font-bold text-slate-900">{zoneId}</p>
                  <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
                </div>
                <div className="space-y-1.5">
                  {KNOWN_METRICS.map(metric => {
                    const value = row?.metrics.find(m => m.metric === metric)?.value ?? null;
                    return (
                      <div key={metric} className="flex items-center justify-between rounded-lg bg-slate-50 px-2.5 py-1.5">
                        <div>
                          <span className="text-xs font-medium text-slate-700">{metricLabel(metric)}</span>
                          <div className="mt-1">
                            <span className={`badge ring-1 ${getMetricQualityTone(metric, value)}`}>
                              {getMetricQualityLabel(metric, value)}
                            </span>
                          </div>
                        </div>
                        <span className="text-xs font-mono font-semibold text-slate-900">
                          {formatMetricValue(metric, value)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
