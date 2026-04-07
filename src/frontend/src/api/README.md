# API — Backend API Client

Axios-based functions that call the FastAPI backend. Each file maps to one backend router. All calls go through the shared `client.ts` instance which automatically attaches the JWT `Authorization` header.

## Files

| File | Backend router | Description |
|------|---------------|-------------|
| `client.ts` | — | Configured axios instance; reads `VITE_API_URL`; attaches JWT from `localStorage` |
| `auth.ts` | `/accounts/login` | Login, logout, token refresh |
| `accounts.ts` | `/accounts` | Account CRUD, registration request submission, admin approval |
| `alerts.ts` | `/alerts` | Fetch alert list, acknowledge alerts |
| `aggregation.ts` | `/aggregation` | Fetch 5-minute and hourly rollup data |
| `thresholds.ts` | `/thresholds` | Threshold CRUD |
| `validation.ts` | `/validation` | Fetch validation event log |
| `publicZones.ts` | `/public/zones` | Public zone status (uses `VITE_PUBLIC_DEMO_API_KEY` header) |
