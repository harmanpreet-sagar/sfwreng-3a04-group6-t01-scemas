"""Pydantic models for validation events and status (Ali — Data Validation)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.enums import ValidationStatus


class ValidationEventBase(BaseModel):
    event_type: str = Field(..., min_length=1)
    message: str
    source: str
    status: ValidationStatus


class ValidationEventCreate(ValidationEventBase):
    pass


class ValidationEventResponse(ValidationEventBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class ValidationStatusSummary(BaseModel):
    valid_count: int
    failed_count: int
    anomaly_count: int
    window_start: datetime
    window_end: datetime
