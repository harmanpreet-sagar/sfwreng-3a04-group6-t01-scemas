/**
 * ZoneMap — Leaflet-based interactive map showing monitoring zones.
 *
 * Each zone is rendered as a CircleMarker centred on its real-world campus
 * coordinates. The marker colour reflects the worst active threshold severity
 * in that zone (critical → red, high → orange, medium → yellow, low → green,
 * none → slate). This gives operators an instant spatial overview without
 * reading the table.
 *
 * Zone → coordinate mapping:
 *  ZONE_COORDS is hardcoded to McMaster University / Hamilton ON campus
 *  coordinates. If new zones are added to KNOWN_ZONES in types/index.ts,
 *  a corresponding entry must be added here, otherwise those zones won't
 *  appear on the map.
 *
 * Click interaction:
 *  Clicking a marker calls onZoneClick(zone), which ThresholdsPage uses to
 *  update the table filter. Clicking the same zone again passes an empty string
 *  to act as a deselect/clear. The selected zone is visually distinguished by a
 *  larger radius and a darker blue border.
 *
 * Leaflet + Vite asset handling:
 *  Vite's module bundler hashes file names at build time, which breaks Leaflet's
 *  hardcoded relative paths to marker-icon.png and marker-shadow.png. We fix
 *  this by importing the images through Vite and manually overriding
 *  L.Marker.prototype.options.icon at module load time.
 *  This is done at module level (not inside the component) because it only
 *  needs to run once, and doing it inside the component would repeat it on
 *  every render. The empty useEffect below is intentional — it exists as a
 *  reminder that some setup runs at module load rather than inside React.
 *
 * scrollWheelZoom is disabled because the map is embedded in a scrollable page;
 * allowing wheel zoom would hijack the user's scroll and feel broken.
 */
import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import type { Threshold } from '../types';

import L from 'leaflet';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconShadowUrl from 'leaflet/dist/images/marker-shadow.png';

// Fix Leaflet default icon paths broken by Vite bundler — runs once at module load.
const _defaultIcon = L.icon({ iconUrl, shadowUrl: iconShadowUrl });
L.Marker.prototype.options.icon = _defaultIcon;

// Real-world coordinates for each campus zone (McMaster / Hamilton ON).
// Order matches KNOWN_ZONES in types/index.ts, but the map renders from this
// record, not from KNOWN_ZONES, so any zone missing here simply won't appear.
const ZONE_COORDS: Record<string, [number, number]> = {
  'zone-a': [43.2634, -79.9196],
  'zone-b': [43.2585, -79.9045],
  'zone-c': [43.2648, -79.9110],
  'zone-d': [43.2562, -79.9215],
};

// Colours match SeverityBadge and SeverityChart for visual consistency
// across all three components.
const SEVERITY_COLOUR: Record<string, string> = {
  low:      '#22c55e',
  medium:   '#eab308',
  high:     '#f97316',
  critical: '#ef4444',
};

interface ZoneInfo {
  zone: string;
  coords: [number, number];
  activeCount: number;
  worstSeverity: string | null; // null when zone has no active thresholds
}

/**
 * Derive per-zone display data from the full threshold list.
 *
 * "Worst severity" is determined by the ORDER array (highest severity first).
 * Array.find returns the first match, so a zone with both critical and low
 * thresholds is coloured critical — the most alarming state takes priority.
 */
function buildZoneInfo(thresholds: Threshold[]): ZoneInfo[] {
  return Object.entries(ZONE_COORDS).map(([zone, coords]) => {
    const active = thresholds.filter(t => t.zone === zone && t.is_active);
    const ORDER = ['critical', 'high', 'medium', 'low'];
    const worst = ORDER.find(s => active.some(t => t.severity === s)) ?? null;
    return { zone, coords, activeCount: active.length, worstSeverity: worst };
  });
}

interface Props {
  thresholds: Threshold[];
  selectedZone: string | null;
  onZoneClick: (zone: string) => void;
}

export default function ZoneMap({ thresholds, selectedZone, onZoneClick }: Props) {
  const zones = buildZoneInfo(thresholds);

  // Intentionally empty — Leaflet icon fix is applied at module level above.
  // This effect exists purely as documentation that some initialisation
  // happens outside the component lifecycle.
  useEffect(() => {
    // no-op: icon fix runs at module load, not per render
  }, []);

  return (
    <MapContainer
      center={[43.2610, -79.9130]}
      zoom={14}
      style={{ height: '100%', width: '100%', borderRadius: '0.75rem' }}
      zoomControl={true}
      scrollWheelZoom={false}
    >
      {/* OpenStreetMap tiles — free, no API key required for a demo deployment */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {zones.map(({ zone, coords, activeCount, worstSeverity }) => {
        // Fall back to slate when the zone has no active thresholds (grey = neutral)
        const colour = worstSeverity ? SEVERITY_COLOUR[worstSeverity] : '#94a3b8';
        const isSelected = selectedZone === zone;

        return (
          <CircleMarker
            key={zone}
            center={coords}
            // Selected marker is larger to indicate which zone filters the table
            radius={isSelected ? 32 : 24}
            pathOptions={{
              color:       isSelected ? '#1d4ed8' : colour,
              fillColor:   colour,
              fillOpacity: isSelected ? 0.85 : 0.55,
              weight:      isSelected ? 3 : 1.5,
            }}
            // Clicking the already-selected zone passes '' which clears the filter
            eventHandlers={{ click: () => onZoneClick(zone === selectedZone ? '' : zone) }}
          >
            {/* permanent tooltip renders as an overlay label, not a hover popup */}
            <Tooltip permanent direction="center" className="!bg-transparent !border-0 !shadow-none">
              <div className="text-center pointer-events-none select-none">
                <div className="text-[10px] font-bold text-white drop-shadow">{zone}</div>
                <div className="text-[9px] text-white/80 drop-shadow">{activeCount} active</div>
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
