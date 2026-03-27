# Pages

Full-page components representing different routes in the application.

## Purpose

Each page component corresponds to a distinct view/route in the application. Pages compose smaller components and handle page-level state management.

## Structure

```tsx
// Example: ThresholdManagement.tsx
import React from 'react'
import { ThresholdList } from '../components/ThresholdList'
import { ThresholdForm } from '../components/ThresholdForm'

export const ThresholdManagement: React.FC = () => {
  return (
    <div className="page-container">
      <h1>Threshold Management</h1>
      <ThresholdForm />
      <ThresholdList />
    </div>
  )
}
```

## Planned Pages

- `Dashboard.tsx` - Main dashboard with telemetry visualizations
- `ThresholdManagement.tsx` - Threshold CRUD interface
- `AlertsView.tsx` - Alert history and management
- `Login.tsx` - User authentication page
- `Settings.tsx` - User account settings
