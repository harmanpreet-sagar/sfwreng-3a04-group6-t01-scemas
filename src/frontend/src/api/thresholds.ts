/**
 * Threshold CRUD API — one function per backend route in routers/thresholds.py.
 *
 * Design notes:
 *  - All functions use the shared apiClient which already carries the Bearer
 *    token set at login, so no manual auth handling is needed here.
 *  - activate / deactivate are intentionally separate endpoints (not a field
 *    on PATCH /threshold/{id}) because the backend writes an audit log
 *    entry for every active-state transition. Routing through dedicated
 *    sub-paths makes those log entries unambiguous.
 *  - ThresholdUpdate (used by updateThreshold) deliberately omits is_active —
 *    toggling active state must go through activateThreshold / deactivateThreshold
 *    to keep the audit trail complete.
 *  - Responses from the backend always return the full updated Threshold object,
 *    so callers can patch their local state list with a simple .map() rather
 *    than triggering a full refetch.
 */
import type { Threshold, ThresholdCreate, ThresholdUpdate } from '../types';
import { apiClient } from './client';

export async function listThresholds(): Promise<Threshold[]> {
  const { data } = await apiClient.get<Threshold[]>('/threshold');
  return data;
}

export async function getThreshold(id: number): Promise<Threshold> {
  const { data } = await apiClient.get<Threshold>(`/threshold/${id}`);
  return data;
}

export async function createThreshold(payload: ThresholdCreate): Promise<Threshold> {
  const { data } = await apiClient.post<Threshold>('/threshold', payload);
  return data;
}

/**
 * Partial update — only sends changed fields.
 * is_active is intentionally excluded from ThresholdUpdate; use
 * activateThreshold / deactivateThreshold to change active state.
 */
export async function updateThreshold(id: number, changes: ThresholdUpdate): Promise<Threshold> {
  const { data } = await apiClient.patch<Threshold>(`/threshold/${id}`, changes);
  return data;
}

export async function activateThreshold(id: number): Promise<Threshold> {
  const { data } = await apiClient.patch<Threshold>(`/threshold/${id}/activate`);
  return data;
}

export async function deactivateThreshold(id: number): Promise<Threshold> {
  const { data } = await apiClient.patch<Threshold>(`/threshold/${id}/deactivate`);
  return data;
}

export async function deleteThreshold(id: number): Promise<void> {
  await apiClient.delete(`/threshold/${id}`);
}
