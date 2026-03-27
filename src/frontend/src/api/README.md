# API Client

HTTP client functions for communicating with the backend API.

## Purpose

Centralized API calls using axios. Each file exports functions that correspond to backend endpoints, providing a clean interface for data fetching and mutations.

## Structure

```typescript
// Example: thresholds.ts
import axios from 'axios'
import { Threshold, ThresholdCreate } from '../types/threshold'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const thresholdApi = {
  // Get all thresholds
  async getAll(): Promise<Threshold[]> {
    const response = await axios.get(`${API_URL}/api/thresholds`)
    return response.data
  },

  // Create new threshold
  async create(data: ThresholdCreate): Promise<Threshold> {
    const response = await axios.post(`${API_URL}/api/thresholds`, data)
    return response.data
  },

  // Delete threshold by ID
  async delete(id: number): Promise<void> {
    await axios.delete(`${API_URL}/api/thresholds/${id}`)
  },
}
```

## Planned API Files

- `thresholds.ts` - Threshold CRUD operations
- `alerts.ts` - Alert fetching and management
- `auth.ts` - Login, logout, token refresh
- `telemetry.ts` - Telemetry data queries
- `mqtt.ts` - MQTT connection management
