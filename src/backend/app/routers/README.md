# Routers — HTTP Route Handlers

Each file in this package defines a FastAPI `APIRouter` for one functional subsystem. Routers validate incoming requests, delegate to the service layer, and format responses. All routers are registered in `backend/main.py`.

## Files

| File | Prefix | Description |
|------|--------|-------------|
| `accounts.py` | `/accounts` | User account CRUD, admin approval/rejection of registration requests |
| `aggregation.py` | `/aggregation` | Queries for 5-minute and hourly aggregated sensor rollups |
| `alerts.py` | `/alerts` | Alert listing, acknowledgement, and SSE stream for live alert push |
| `public_demo.py` | `/public/demo` | Unauthenticated demo endpoints (no API key required) |
| `public_zones.py` | `/public/zones` | Zone status for the public landing map (API key protected, rate-limited) |
| `thresholds.py` | `/thresholds` | Threshold CRUD (create, read, update, delete, toggle active) |
| `validation.py` | `/validation` | Data validation event log queries |

## Conventions

- All protected routes use `Depends(get_current_user)` from `shared/auth.py` for JWT verification.
- Public API routes use `Depends(verify_public_api_key)` from `shared/deps_public_api.py`.
- Routers use `async def` handlers throughout
- Database calls go through the async pool in `shared/db.py`.
