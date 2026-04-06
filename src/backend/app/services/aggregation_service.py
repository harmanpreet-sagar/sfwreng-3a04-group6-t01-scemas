"""Aggregation orchestration: compute rollups and shape endpoint responses."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from app.services import aggregated_data_repository
from app.shared.aggregation import (
    AggregationHistoryPoint,
    AggregationHistoryResponse,
    AggregationPoint,
    AggregationZoneSummary,
    AggregationZonesResponse,
)

logger = logging.getLogger(__name__)

FIVE_MINUTES = timedelta(minutes=5)
ONE_HOUR = timedelta(hours=1)


def _floor_time(dt: datetime, bucket: timedelta) -> datetime:
    bucket_seconds = int(bucket.total_seconds())
    ts = int(dt.timestamp())
    return datetime.fromtimestamp(ts - (ts % bucket_seconds), tz=UTC)


def run_aggregation_cycle(now: datetime | None = None) -> None:
    """
    Compute completed 5-minute buckets and the hourly max on each hour boundary.
    """
    now = now or datetime.now(UTC)
    current_five_minute_end = _floor_time(now, FIVE_MINUTES)
    latest_five_minute_end = aggregated_data_repository.fetch_latest_bucket_end(
        aggregation_window="5m",
        aggregation_type="avg",
    )

    # Always operate on fully completed windows only, never the in-progress one.
    next_five_minute_end = (
        current_five_minute_end
        if latest_five_minute_end is None
        else latest_five_minute_end + FIVE_MINUTES
    )

    while next_five_minute_end <= current_five_minute_end:
        window_start = next_five_minute_end - FIVE_MINUTES
        _compute_and_store_five_minute_rollups(
            window_start=window_start,
            window_end=next_five_minute_end,
        )

        if next_five_minute_end.minute == 0:
            _compute_and_store_hourly_max(
                window_start=next_five_minute_end - ONE_HOUR,
                window_end=next_five_minute_end,
            )

        next_five_minute_end += FIVE_MINUTES


def _compute_and_store_five_minute_rollups(
    *, window_start: datetime, window_end: datetime
) -> None:
    rows = aggregated_data_repository.fetch_five_minute_rollups(
        window_start=window_start,
        window_end=window_end,
    )
    for row in rows:
        aggregated_data_repository.upsert_aggregate_row(
            zone=row.zone,
            metric=row.metric,
            aggregation_window="5m",
            aggregation_type="avg",
            value=float(row.avg_value),
            window_start=window_start,
            window_end=window_end,
        )
        aggregated_data_repository.upsert_aggregate_row(
            zone=row.zone,
            metric=row.metric,
            aggregation_window="5m",
            aggregation_type="max",
            value=float(row.max_value),
            window_start=window_start,
            window_end=window_end,
        )


def _compute_and_store_hourly_max(
    *, window_start: datetime, window_end: datetime
) -> None:
    rows = aggregated_data_repository.fetch_hourly_max_rollups(
        window_start=window_start,
        window_end=window_end,
    )
    for row in rows:
        aggregated_data_repository.upsert_aggregate_row(
            zone=row.zone,
            metric=row.metric,
            aggregation_window="1h",
            aggregation_type="max",
            value=float(row.max_value),
            window_start=window_start,
            window_end=window_end,
        )


def list_latest_zone_aggregates() -> AggregationZonesResponse:
    rows = aggregated_data_repository.fetch_latest_row_per_zone_metric()
    return _group_rows_by_zone(rows)


def get_latest_zone_aggregates(zone: str) -> AggregationZoneSummary | None:
    rows = aggregated_data_repository.fetch_latest_row_per_metric_for_zone(zone)
    if not rows:
        return None
    grouped = _group_rows_by_zone(rows)
    return grouped.zones[0]


def get_zone_metric_history(
    zone: str,
    metric: str,
    *,
    limit: int,
    aggregation_window: str = "5m",
    aggregation_type: str = "avg",
) -> AggregationHistoryResponse:
    rows = aggregated_data_repository.fetch_history_for_zone_metric(
        zone,
        metric,
        limit=limit,
        aggregation_window=aggregation_window,
        aggregation_type=aggregation_type,
    )
    points = [
        AggregationHistoryPoint(
            value=float(r["value"]),
            window_start=r["window_start"],
            window_end=r["window_end"],
        )
        for r in reversed(rows)
    ]
    return AggregationHistoryResponse(
        zone=zone,
        metric=metric,
        aggregation_window=aggregation_window,
        aggregation_type=aggregation_type,
        points=points,
        total=len(points),
    )


def _group_rows_by_zone(rows: list[dict]) -> AggregationZonesResponse:
    by_zone: dict[str, list[AggregationPoint]] = defaultdict(list)
    for row in rows:
        zone = str(row["zone"])
        by_zone[zone].append(
            AggregationPoint(
                metric=str(row["metric"]),
                value=float(row["value"]),
                aggregation_window=str(row["aggregation_window"]),
                aggregation_type=str(row["aggregation_type"]),
                window_start=row["window_start"],
                window_end=row["window_end"],
            )
        )

    zones: list[AggregationZoneSummary] = []
    for zone in sorted(by_zone.keys()):
        metrics = sorted(by_zone[zone], key=lambda m: m.metric)
        zones.append(
            AggregationZoneSummary(
                zone=zone,
                metrics=metrics,
                updated_at=max(m.window_end for m in metrics),
            )
        )
    return AggregationZonesResponse(zones=zones, total=len(zones))
