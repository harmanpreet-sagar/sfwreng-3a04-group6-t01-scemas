/**
 * Public-facing zone map for the marketing landing page.
 * Uses /public/zones data when VITE_PUBLIC_DEMO_API_KEY is set; otherwise shows coverage only.
 */
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import { CAMPUS_CENTER, ZONE_COORDS } from '../constants/zoneMap';
import '../map/leafletDefaultIcon';
import type { PublicZoneSummary } from '../api/publicZones';
import { staticZoneIds } from '../api/publicZones';

const SEVERITY_FILL: Record<string, string> = {
  low: '#22c55e',
  medium: '#0ea5e9',
  high: '#f97316',
  critical: '#ef4444',
};

const NEUTRAL = '#94a3b8';
const NORMAL_OK = '#14b8a6';

interface Props {
  /** Live summaries from public API, or null to show static coverage */
  zones: PublicZoneSummary[] | null;
}

export default function PublicLandingMap({ zones }: Props) {
  const byZone = zones ? Object.fromEntries(zones.map(z => [z.zone, z])) : null;
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
        const row = byZone?.[zoneId];
        let fill = NEUTRAL;
        let subtitle = 'Monitoring coverage';
        if (row) {
          if (row.status === 'alerting' && row.active_alert_highest_severity) {
            fill = SEVERITY_FILL[row.active_alert_highest_severity] ?? NEUTRAL;
            subtitle = `Alerting · ${row.active_alert_highest_severity}`;
          } else {
            fill = NORMAL_OK;
            subtitle = 'Normal';
          }
          if (row.metrics.length) {
            subtitle += ` · ${row.metrics.length} metric${row.metrics.length === 1 ? '' : 's'}`;
          }
        }

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
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
