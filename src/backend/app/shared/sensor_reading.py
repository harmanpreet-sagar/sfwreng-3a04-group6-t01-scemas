"""Pydantic models for raw sensor readings (Ali — Data Validation)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SensorReadingBase(BaseModel):
    zone: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float
    unit: Optional[str] = None


class SensorReadingCreate(SensorReadingBase):
    raw_payload: Optional[str] = None


class SensorReadingResponse(SensorReadingBase):
    id: int
    timestamp: datetime
    is_valid: bool
    validation_message: Optional[str] = None

    class Config:
        from_attributes = True
