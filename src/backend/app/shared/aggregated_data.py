"""Pydantic models for aggregated environmental data."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AggregatedDataBase(BaseModel):
    zone: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    aggregation_window: str = Field(..., min_length=1)
    aggregation_type: str = Field(..., min_length=1)
    value: float
    window_start: datetime
    window_end: datetime


class AggregatedDataCreate(AggregatedDataBase):
    pass


class AggregatedDataResponse(AggregatedDataBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
