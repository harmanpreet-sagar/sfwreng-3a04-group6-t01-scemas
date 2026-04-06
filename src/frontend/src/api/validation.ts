/**
 * Validation API — current pipeline health counters.
 */
import { apiClient } from './client';
import type { ValidationEventRecord, ValidationStatusResponse } from '../types';

export async function getValidationStatus(): Promise<ValidationStatusResponse> {
  const { data } = await apiClient.get<ValidationStatusResponse>('/validation/status');
  return data;
}

export async function getValidationEvents(): Promise<ValidationEventRecord[]> {
  const { data } = await apiClient.get<ValidationEventRecord[]>('/validation/events');
  return data;
}
