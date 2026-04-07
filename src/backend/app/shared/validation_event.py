"""Pydantic models for validation events and status summaries."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.enums import ValidationStatus

# `public.validation_events.status` is written in uppercase by the ingestion
# pipeline (see `validation_service.write_validation_event`). Threshold evaluation
# and similar readers should filter using these literals, not the Pydantic enum
# value strings (which are lowercase).
VALIDATION_EVENTS_DB_STATUS_VALID = "VALID"


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
