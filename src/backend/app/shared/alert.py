"""Pydantic models for the Alerts subsystem (Aakash)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.shared.enums import AlertSeverity, AlertStatus


class AlertBase(BaseModel):
    zone: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    severity: AlertSeverity
    message: str = Field(..., min_length=1)
    status: AlertStatus = AlertStatus.active
    source_type: Optional[str] = None
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

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
