"""Public, read-only zone summaries for signage / external dashboards.

Simple explanation: Describes the simple public view of a zone—mostly latest numbers,
plus a plain “all good” vs “something’s wrong” hint from active alerts (without spilling
private alert details).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.shared.enums import AlertSeverity


class PublicZoneOperationalStatus(str, Enum):
    """High-level cue derived from active alerts (no internal alert text)."""

    normal = "normal"
    alerting = "alerting"


class PublicZoneMetricReading(BaseModel):
    """Latest aggregated value for one metric in a zone."""

    metric: str = Field(..., description="Metric name (e.g. temperature, co2)")
    value: float = Field(..., description="Aggregated value for the latest window")
    window_end: datetime = Field(
        ...,
        description="End of the aggregation window (freshness of this reading)",
    )


class PublicZoneSummary(BaseModel):
    """One zone: all current metrics plus optional alert severity rollup."""

    zone: str
    metrics: List[PublicZoneMetricReading] = Field(
        default_factory=list,
        description="Latest reading per metric from aggregated_data",
    )
    updated_at: datetime = Field(
        ...,
        description="Latest window_end among metrics (overall as-of time for the zone)",
    )
    status: PublicZoneOperationalStatus = Field(
        ...,
        description="normal if no active alerts in this zone, else alerting",
    )
    active_alert_highest_severity: Optional[AlertSeverity] = Field(
        None,
        description="Worst active alert severity in this zone, if any",
    )


class PublicZonesListResponse(BaseModel):
    """Stable list envelope for GET /public/zones."""

    zones: List[PublicZoneSummary]
    total: int = Field(..., description="Number of zones in this response")
