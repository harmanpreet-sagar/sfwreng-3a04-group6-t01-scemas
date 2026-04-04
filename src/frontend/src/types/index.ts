/**
 * Shared TypeScript types for the Threshold Management frontend.
 *
 * These mirror the Pydantic models defined in the backend's app/shared/ layer.
 * Keeping them in one place means any API contract change is a single update
 * here rather than hunting across every component that calls the API.
 */

// Severity matches AlertSeverity in backend/app/shared/enums.py
export type Severity = 'low' | 'medium' | 'high' | 'critical';

// Condition matches ThresholdCondition in backend/app/shared/enums.py
export type Condition = 'gt' | 'gte' | 'lt' | 'lte' | 'eq';

// Clearance matches the `clearance` column in the accounts table (Jason's schema).
// Note: this is lowercase ("admin"/"operator"), unlike UserRole in auth.py ("ADMIN"/"OPERATOR").
// The mapping happens in accounts.py at login time.
export type Clearance = 'admin' | 'operator';

// Full threshold row returned by GET /threshold and POST /threshold
export interface Threshold {
  id: number;
  zone: string;
  metric: string;
  condition: Condition;
  threshold_value: number;
  severity: Severity;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Body for POST /threshold — mirrors ThresholdCreate in backend/app/shared/threshold.py
export interface ThresholdCreate {
  zone: string;
  metric: string;
  condition: Condition;
  threshold_value: number;
  severity: Severity;
  is_active: boolean;
}

// Body for PATCH /threshold/{id} — all fields optional (partial update).
// is_active is intentionally excluded: the backend manages it exclusively
// through the /activate and /deactivate sub-routes so the audit log is always
// populated for active-state changes.
export interface ThresholdUpdate {
  zone?: string;
  metric?: string;
  condition?: Condition;
  threshold_value?: number;
  severity?: Severity;
}

// Account row returned by POST /account/login
export interface Account {
  aid: number;
  name: string;
  email: string;
  clearance: Clearance;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Full login response — access_token is present when JWT_SECRET is set in the backend env.
// Without it the threshold endpoints (which require Bearer auth) will return 401.
export interface LoginResponse {
  message: string;
  identity_verified: boolean;
  account: Account;
  access_token?: string;
  token_type?: string;
}

// ── UI-layer constants ────────────────────────────────────────────────────────

// Zones match what the simulator publishes and what the evaluator reads.
// Updating this list here also updates every dropdown in the form modal.
export const KNOWN_ZONES = ['zone-a', 'zone-b', 'zone-c', 'zone-d'] as const;

// Metrics match VALID_RANGES in backend/app/services/validation_service.py.
// A value outside a metric's physical range is rejected there before it
// ever reaches the aggregation layer.
export const KNOWN_METRICS = ['aqi', 'temperature', 'humidity', 'noise'] as const;

// Human-readable labels for each condition operator used in the form dropdown
export const CONDITIONS: { value: Condition; label: string }[] = [
  { value: 'gt',  label: '> (greater than)' },
  { value: 'gte', label: '>= (greater than or equal)' },
  { value: 'lt',  label: '< (less than)' },
  { value: 'lte', label: '<= (less than or equal)' },
  { value: 'eq',  label: '= (equal to)' },
];

export const SEVERITIES: Severity[] = ['low', 'medium', 'high', 'critical'];

// ── Alerts (GET /alerts, SSE payloads) ───────────────────────────────────────

export type AlertStatus = 'active' | 'acknowledged' | 'resolved';

export interface Alert {
  id: number;
  zone: string;
  metric: string;
  severity: Severity;
  message: string;
  status: AlertStatus;
  source_type: string | null;
  observed_value: number | null;
  threshold_value: number | null;
  threshold_id: number | null;
  created_at: string;
  updated_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

/** One row from GET /alerts — wrapper matches FastAPI AlertListResponse */
export interface AlertListResponse {
  alerts: Alert[];
  total: number;
}

/**
 * JSON payload on SSE `data:` lines from GET /alerts/stream
 * (see build_alert_sse_event in the backend).
 */
export interface SseAlertEvent {
  event_type: 'alert.created' | 'alert.acknowledged' | 'alert.resolved' | string;
  id: number;
  status: AlertStatus;
  severity: Severity;
  zone: string;
  metric: string;
  message: string;
  observed_value: number | null;
  threshold_value: number | null;
  threshold_id: number | null;
  created_at: string;
  updated_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}
