/**
 * Shared Hamilton / McMaster coordinates for Leaflet maps (landing + operator views).
 */

export const CAMPUS_CENTER: [number, number] = [43.261, -79.913];

/** Zone id → [lat, lng] — keep in sync with backend aggregated_data / simulator zones */
export const ZONE_COORDS: Record<string, [number, number]> = {
  'zone-a': [43.2634, -79.9196],
  'zone-b': [43.2585, -79.9045],
  'zone-c': [43.2648, -79.911],
  'zone-d': [43.2562, -79.9215],
};
