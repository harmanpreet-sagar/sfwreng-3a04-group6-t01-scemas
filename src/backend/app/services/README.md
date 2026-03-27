# Services

Business logic layer implementing subsystem operations.

## Purpose

Services encapsulate business logic, coordinate between repositories and external APIs, and implement the core functionality of each subsystem (Threshold Management, Alerts, etc.).

## Structure

```python
# Example: threshold_service.py
from ..models.threshold import ThresholdCreate, Threshold
from .database import supabase

class ThresholdService:
    @staticmethod
    async def create(threshold_data: ThresholdCreate) -> Threshold:
        # Validate business rules
        # Save to database
        # Return created threshold
        pass
    
    @staticmethod
    async def evaluate(telemetry_data: dict) -> list:
        # Compare telemetry against thresholds
        # Generate alerts if thresholds violated
        pass
```

## Planned Services

- `threshold_service.py` - Threshold CRUD and evaluation logic
- `alert_service.py` - Alert generation and management
- `account_service.py` - User authentication and authorization
- `mqtt_service.py` - MQTT client for telemetry streaming
- `notification_service.py` - SMS notifications via Twilio
