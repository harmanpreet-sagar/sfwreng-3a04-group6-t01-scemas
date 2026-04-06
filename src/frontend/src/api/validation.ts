/**
 * Validation API — current pipeline health counters.
 */
import { apiClient } from './client';
import type { ValidationStatusResponse } from '../types';

export async function getValidationStatus(): Promise<ValidationStatusResponse> {
  const { data } = await apiClient.get<ValidationStatusResponse>('/validation/status');
  return data;
}
