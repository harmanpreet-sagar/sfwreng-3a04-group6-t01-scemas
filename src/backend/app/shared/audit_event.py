"""Pydantic models for audit log entries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuditEventBase(BaseModel):
    event_type: str = Field(..., min_length=1)
    actor_id: int
    actor_email: str
    target_id: Optional[int] = None
    target_type: Optional[str] = None
    message: str


class AuditEventCreate(AuditEventBase):
    pass


class AuditEventResponse(AuditEventBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditEventListResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int
