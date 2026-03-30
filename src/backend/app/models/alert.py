from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertBase(BaseModel):
    zone: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    severity: AlertSeverity
    message: str = Field(..., min_length=1)
    status: AlertStatus = AlertStatus.active
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    threshold_id: Optional[int] = None


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

