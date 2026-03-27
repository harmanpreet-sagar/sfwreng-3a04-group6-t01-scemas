# Routers

API route handlers for different subsystems.

## Purpose

Each router file defines HTTP endpoints for a specific functional area. Routers handle request validation, call service layer functions, and format responses.

## Structure

```python
# Example: thresholds.py
from fastapi import APIRouter, HTTPException, Depends
from ..services.threshold_service import ThresholdService
from ..models.threshold import ThresholdCreate, ThresholdResponse

router = APIRouter(prefix="/api/thresholds", tags=["Thresholds"])

@router.post("/", response_model=ThresholdResponse)
async def create_threshold(threshold: ThresholdCreate):
    # Call service layer
    return await ThresholdService.create(threshold)
```

## Planned Routers

- `thresholds.py` - Threshold CRUD operations
- `alerts.py` - Alert management endpoints
- `accounts.py` - User account operations
- `dashboard.py` - Dashboard data aggregation
