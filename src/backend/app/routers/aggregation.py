"""Read-only aggregation endpoints for dashboard charts and maps."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.services.aggregation_service import (
    get_latest_zone_aggregates,
    get_zone_metric_history,
    list_latest_zone_aggregates,
)
from app.shared.aggregation import (
    AggregationHistoryResponse,
    AggregationZoneSummary,
    AggregationZonesResponse,
)
from app.shared.auth import CurrentUser, require_operator_or_admin

router = APIRouter(prefix="/aggregation", tags=["Aggregation"])


@router.get("/zones", response_model=AggregationZonesResponse)
def get_aggregation_zones(
    _: CurrentUser = Depends(require_operator_or_admin),
) -> AggregationZonesResponse:
    return list_latest_zone_aggregates()


@router.get("/zones/{zone}", response_model=AggregationZoneSummary)
def get_aggregation_zone(
    zone: Annotated[str, Path(..., min_length=1, max_length=256)],
    _: CurrentUser = Depends(require_operator_or_admin),
) -> AggregationZoneSummary:
    summary = get_latest_zone_aggregates(zone.strip())
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "zone_not_found",
                "message": "No aggregated data exists for this zone.",
                "zone": zone.strip(),
            },
        )
    return summary


@router.get("/zones/{zone}/history", response_model=AggregationHistoryResponse)
def get_aggregation_zone_history(
    zone: Annotated[str, Path(..., min_length=1, max_length=256)],
    metric: Annotated[str, Query(..., min_length=1)],
    aggregation_window: Annotated[str, Query(min_length=1)] = "5m",
    aggregation_type: Annotated[str, Query(min_length=1)] = "avg",
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    _: CurrentUser = Depends(require_operator_or_admin),
) -> AggregationHistoryResponse:
    return get_zone_metric_history(
        zone.strip(),
        metric.strip(),
        limit=limit,
        aggregation_window=aggregation_window.strip(),
        aggregation_type=aggregation_type.strip(),
    )
