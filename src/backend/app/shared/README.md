# Shared — Cross-Cutting Utilities

Modules in this package are used by routers, services, and tasks across the entire application. They cover authentication, database access, shared data models, middleware, and startup seeding.

## Files

| File | Description |
|------|-------------|
| `auth.py` | JWT creation, verification, and the `get_current_user` FastAPI dependency |
| `db.py` | Async PostgreSQL connection pool (asyncpg); provides `get_db_conn` dependency |
| `enums.py` | Shared enumerations: `MetricType`, `SeverityLevel`, `ZoneStatus`, etc. |
| `account.py` | Pydantic model for the authenticated user principal |
| `account_dependencies.py` | FastAPI dependencies for role-based access (admin vs. regular user) |
| `aggregated_data.py` | Pydantic models for aggregated rollup responses |
| `aggregation.py` | Shared aggregation data structures |
| `alert.py` | Pydantic models for alert request/response |
| `alert_sse_broadcaster.py` | In-process SSE broadcaster; routers subscribe, `alert_service` publishes |
| `api_key_hash.py` | Hashing utilities for public API keys |
| `api_key_seed.py` | Default demo API key used when `DEMO_PUBLIC_API_KEY` env var is unset |
| `audit.py` | Audit log writing helpers |
| `audit_event.py` | Pydantic model for audit log entries |
| `deps_public_api.py` | FastAPI dependency that validates `X-API-Key` headers for public routes |
| `public_api_audit_middleware.py` | Starlette middleware that logs every public API request |
| `public_api_errors.py` | Standardised error responses for public API failures |
| `public_api_rate_limiter.py` | In-memory sliding-window rate limiter for public API keys |
| `seed_accounts.py` | Seeds default admin account at application startup if none exists |
| `sensor_reading.py` | Pydantic model for raw MQTT sensor readings |
| `threshold.py` | Pydantic models for threshold request/response |
| `threshold_seed.py` | Seeds a set of default thresholds at startup |
| `validation_event.py` | Pydantic models for validation event records |
