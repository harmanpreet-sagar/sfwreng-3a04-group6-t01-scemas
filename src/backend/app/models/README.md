# Models

Pydantic models for request/response validation and database schemas.

## Purpose

Define data structures, validation rules, and type hints for API contracts and database entities.

## Structure

```python
# Example: threshold.py
from pydantic import BaseModel, Field
from datetime import datetime

class ThresholdBase(BaseModel):
    metric_type: str
    zone: str
    condition: str
    severity_level: str

class ThresholdCreate(ThresholdBase):
    pass

class ThresholdResponse(ThresholdBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## Planned Models

- `threshold.py` - Threshold entity and validation
- `alert.py` - Alert entity
- `user.py` - User account entity
- `telemetry.py` - Sensor data models
