# Services — Business Logic and Repository Layer

This package contains the business logic for every SCEMAS subsystem. Services are called by routers and coordinate database access through repository modules.

## Files

| File | Description |
|------|-------------|
| `accounts_service.py` | Account registration, approval workflow, password hashing |
| `aggregated_data_repository.py` | DB queries for 5-minute and hourly rollup tables |
| `aggregation_service.py` | Computes and persists windowed aggregations from raw readings |
| `alert_repository.py` | DB queries for alert records (insert, fetch, acknowledge) |
| `alert_service.py` | Alert creation logic; dispatches SSE broadcast and SMS notification |
| `api_key_repository.py` | DB queries for hashed public API keys |
| `notification_service.py` | Twilio SMS dispatch for critical alerts |
| `public_zones_service.py` | Aggregates zone health status for the public map endpoint |
| `threshold_evaluation.py` | Evaluates a sensor reading against all active thresholds |
| `threshold_repository.py` | DB queries for threshold records |
| `threshold_service.py` | Threshold CRUD; delegates evaluation to `threshold_evaluation.py` |
| `validation_events_repository.py` | DB queries for validation event records |
| `validation_service.py` | Classifies incoming readings as valid/anomalous; persists events |
