# Types

TypeScript type definitions and interfaces.

## Purpose

Centralized type definitions ensure type safety across the application and document the shape of data structures. These types should match the backend API contracts.

## Structure

```typescript
// Example: threshold.ts
export interface Threshold {
  id: number
  metricType: string
  zone: string
  condition: string
  severityLevel: 'low' | 'medium' | 'high' | 'critical'
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface ThresholdCreate {
  metricType: string
  zone: string
  condition: string
  severityLevel: string
}

export interface ThresholdUpdate extends Partial<ThresholdCreate> {
  id: number
}
```

## Planned Type Files

- `threshold.ts` - Threshold entity types
- `alert.ts` - Alert entity types
- `user.ts` - User and authentication types
- `telemetry.ts` - Sensor data types
- `api.ts` - API response wrapper types
