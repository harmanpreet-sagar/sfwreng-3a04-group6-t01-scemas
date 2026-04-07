# Types — TypeScript Type Definitions

Centralised TypeScript interfaces and type aliases shared across the frontend.

## Files

| File | Description |
|------|-------------|
| `index.ts` | All shared interfaces: `Alert`, `Threshold`, `Account`, `SensorReading`, `AggregatedDataPoint`, `PublicZone`, `ValidationEvent`, and API response wrappers |

Keeping all types in a single `index.ts` makes imports predictable (`import type { Alert } from '../types'`) and ensures the frontend's type contracts stay in sync with the backend's Pydantic schemas.
