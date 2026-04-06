/**
 * Alerts API — list, acknowledge, resolve (JWT Bearer via shared apiClient).
 */
import { apiClient } from './client';
import type { Alert, AlertListResponse } from '../types';

export async function listAlerts(params?: {
  status?: string;
  zone?: string;
  severity?: string;
}): Promise<AlertListResponse> {
  const { data } = await apiClient.get<AlertListResponse>('/alerts', { params });
  return data;
}

export async function acknowledgeAlert(id: number): Promise<Alert> {
  const { data } = await apiClient.patch<Alert>(`/alerts/${id}/acknowledge`);
  return data;
}

export async function resolveAlert(id: number): Promise<Alert> {
  const { data } = await apiClient.patch<Alert>(`/alerts/${id}/resolve`);
  return data;
}
