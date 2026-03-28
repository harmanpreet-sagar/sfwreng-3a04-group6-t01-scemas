# Tests

Automated test suite for backend and frontend.

## Purpose

Ensure code quality and prevent regressions through comprehensive test coverage. Tests should cover unit tests, integration tests, and end-to-end scenarios.

## Structure

```
tests/
├── backend/
│   ├── test_thresholds.py      # Threshold service tests
│   ├── test_alerts.py          # Alert generation tests
│   ├── test_api_facade.py      # API routing tests
│   └── test_mqtt.py            # MQTT integration tests
├── frontend/
│   ├── components/             # Component unit tests
│   ├── pages/                  # Page integration tests
│   └── api/                    # API client tests
└── e2e/
    └── threshold_workflow.spec.ts  # End-to-end user flows
```

## Backend Testing (pytest)

```python
# Example test file
import pytest
from app.services.threshold_service import ThresholdService

@pytest.mark.asyncio
async def test_create_threshold():
    threshold_data = {
        "metric_type": "temperature",
        "zone": "warehouse-1",
        "condition": "> 25",
        "severity_level": "high"
    }
    result = await ThresholdService.create(threshold_data)
    assert result.id is not None
    assert result.metric_type == "temperature"
```

## Frontend Testing (Vitest + React Testing Library)

```typescript
// Example component test
import { render, screen } from '@testing-library/react'
import { ThresholdCard } from './ThresholdCard'

test('renders threshold information', () => {
  const threshold = {
    id: 1,
    metricType: 'temperature',
    zone: 'warehouse-1',
    condition: '> 25',
    severityLevel: 'high'
  }
  
  render(<ThresholdCard threshold={threshold} />)
  expect(screen.getByText('temperature')).toBeInTheDocument()
})
```

## Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```
