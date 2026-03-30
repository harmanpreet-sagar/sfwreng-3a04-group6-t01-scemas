"""Pydantic models for the Aggregation Management subsystem (Praneet)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AggregatedDataBase(BaseModel):
    zone: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float


class AggregatedDataCreate(AggregatedDataBase):
    window_end: datetime


class AggregatedDataResponse(AggregatedDataBase):
    id: int
    window_end: datetime
    created_at: datetime

    class Config:
        from_attributes = True
