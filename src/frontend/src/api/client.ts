/**
 * Central axios instance used by every API module in this application.
 *
 * All requests go through a single instance so that:
 *  1. The Authorization header only needs to be set once (via setAuthToken)
 *     and automatically applies to every subsequent call, including threshold
 *     CRUD operations that require a Bearer token.
 *  2. The base URL is resolved at startup from the VITE_API_URL env variable
 *     injected by Docker Compose, allowing the same build to target different
 *     backend URLs without code changes.
 *
 * VITE_ prefix is mandatory: Vite's bundler strips all other env variables
 * from the browser bundle for security. Without it, import.meta.env.VITE_API_URL
 * would be undefined at runtime even if the variable is set in .env.
 */
import axios from 'axios';

export const API_BASE =
  (import.meta as { env: Record<string, string> }).env.VITE_API_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Attach or clear the JWT Bearer token on the shared axios instance.
 *
 * Called by AuthContext.signIn after a successful login (to attach the token)
 * and by AuthContext.signOut (to remove it). Modifying `defaults.headers.common`
 * here means every future request automatically carries the token without any
 * per-call wiring. The token is also restored from localStorage on page refresh
 * via the useEffect in AuthProvider.
 */
export function setAuthToken(token: string | null): void {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
}
