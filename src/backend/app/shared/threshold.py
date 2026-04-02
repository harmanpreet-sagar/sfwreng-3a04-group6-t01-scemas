"""Pydantic models for the Threshold Management subsystem (Harmanpreet)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.shared.enums import AlertSeverity, ThresholdCondition


class ThresholdBase(BaseModel):
    zone: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    condition: ThresholdCondition
    threshold_value: float
    severity: AlertSeverity
    is_active: bool = True


class ThresholdCreate(ThresholdBase):
    pass


class ThresholdUpdate(BaseModel):
    zone: Optional[str] = None
    metric: Optional[str] = None
    condition: Optional[ThresholdCondition] = None
    threshold_value: Optional[float] = None
    severity: Optional[AlertSeverity] = None


class ThresholdResponse(ThresholdBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
