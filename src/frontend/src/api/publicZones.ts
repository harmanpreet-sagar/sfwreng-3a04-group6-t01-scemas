/**
 * Read-only public zone summaries (Bearer API key — not the operator JWT).
 *
 * VITE_PUBLIC_DEMO_API_KEY should match DEMO_PUBLIC_API_KEY in src/.env when you
 * want the landing page to show live status; if unset, the map falls back to static zones.
 */
import axios from 'axios';
import { KNOWN_ZONES } from '../types';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const PUBLIC_KEY = (import.meta.env.VITE_PUBLIC_DEMO_API_KEY ?? '').trim();

export type PublicOperationalStatus = 'normal' | 'alerting';

export interface PublicZoneMetricReading {
  metric: string;
  value: number;
  window_end: string;
}

export interface PublicZoneSummary {
  zone: string;
  metrics: PublicZoneMetricReading[];
  updated_at: string;
  status: PublicOperationalStatus;
  active_alert_highest_severity: 'low' | 'medium' | 'high' | 'critical' | null;
}

export interface PublicZonesListResponse {
  zones: PublicZoneSummary[];
  total: number;
}

export function isPublicApiConfigured(): boolean {
  return PUBLIC_KEY.length > 0;
}

export async function fetchPublicZones(): Promise<PublicZoneSummary[] | null> {
  if (!PUBLIC_KEY) return null;
  try {
    const { data } = await axios.get<PublicZonesListResponse>(`${API_BASE}/public/zones`, {
      headers: { Authorization: `Bearer ${PUBLIC_KEY}` },
      timeout: 12_000,
    });
    return data.zones;
  } catch {
    return null;
  }
}

/** Zones to show on the map when the API is unavailable — still “coverage” for the PoC */
export function staticZoneIds(): string[] {
  return [...KNOWN_ZONES];
}
