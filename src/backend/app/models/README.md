# Models — Pydantic API Models

Pydantic models used as request/response schemas for the public-facing API endpoints.

## Files

| File | Description |
|------|-------------|
| `public_api_key.py` | Request and response models for public API key management |
| `public_zone.py` | Response model for public zone status (used by the landing map) |

Most application-wide schemas (alerts, thresholds, sensor readings, accounts, etc.) live in `app/shared/` alongside the code that uses them, following the co-location convention adopted by this project.
