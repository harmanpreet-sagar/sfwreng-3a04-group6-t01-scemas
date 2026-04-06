/**
 * Aggregation API — latest zone summaries for dashboard maps and gauges.
 */
import { apiClient } from './client';
import type {
  AggregationHistoryResponse,
  AggregationZoneSummary,
  AggregationZonesResponse,
} from '../types';

export async function getAggregationZones(): Promise<AggregationZonesResponse> {
  const { data } = await apiClient.get<AggregationZonesResponse>('/aggregation/zones');
  return data;
}

export async function getAggregationZone(zone: string): Promise<AggregationZoneSummary> {
  const { data } = await apiClient.get<AggregationZoneSummary>(`/aggregation/zones/${encodeURIComponent(zone)}`);
  return data;
}

export async function getAggregationHistory(
  zone: string,
  metric: string,
  limit = 24,
  aggregationWindow = '5m',
  aggregationType = 'avg',
): Promise<AggregationHistoryResponse> {
  const { data } = await apiClient.get<AggregationHistoryResponse>(
    `/aggregation/zones/${encodeURIComponent(zone)}/history`,
    { params: { metric, limit, aggregation_window: aggregationWindow, aggregation_type: aggregationType } },
  );
  return data;
}
