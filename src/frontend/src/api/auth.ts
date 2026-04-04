/**
 * Authentication API — thin wrapper around POST /account/login.
 *
 * Intentionally a separate module from thresholds.ts so that the login call
 * can be made before a JWT is available (the Authorization header is absent
 * at this point; the backend's /login endpoint is the one public route).
 *
 * The response includes both the account profile and an optional access_token.
 * The token is absent only when JWT_SECRET is not set in the backend's
 * environment (e.g. a misconfigured deployment). In that case all subsequent
 * threshold API calls will return 401 and the user will be signed out.
 */
import type { LoginResponse } from '../types';
import { apiClient } from './client';

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/account/login', { email, password });
  return data;
}
