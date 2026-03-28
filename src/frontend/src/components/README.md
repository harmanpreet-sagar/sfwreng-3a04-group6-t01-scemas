# Components

Reusable UI components used across multiple pages.

## Purpose

Small, focused, reusable React components that implement specific UI elements. Components should be composable and follow single-responsibility principle.

## Structure

```tsx
// Example: ThresholdCard.tsx
import React from 'react'
import { Threshold } from '../types/threshold'

interface ThresholdCardProps {
  threshold: Threshold
  onEdit: (id: number) => void
  onDelete: (id: number) => void
}

export const ThresholdCard: React.FC<ThresholdCardProps> = ({ 
  threshold, 
  onEdit, 
  onDelete 
}) => {
  return (
    <div className="threshold-card">
      <h3>{threshold.metricType}</h3>
      <p>Zone: {threshold.zone}</p>
      <button onClick={() => onEdit(threshold.id)}>Edit</button>
      <button onClick={() => onDelete(threshold.id)}>Delete</button>
    </div>
  )
}
```

## Planned Components

- `ThresholdCard.tsx` - Display threshold information
- `ThresholdForm.tsx` - Form for creating/editing thresholds
- `ThresholdList.tsx` - List of all thresholds
- `AlertCard.tsx` - Display alert information
- `Navigation.tsx` - Top navigation bar
- `TelemetryChart.tsx` - Real-time telemetry visualization
