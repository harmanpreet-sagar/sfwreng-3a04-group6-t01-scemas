"""Persistence helpers for `public.aggregated_data` and source readings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from psycopg.rows import dict_row

from app.shared.db import db_connection

DEFAULT_WINDOW = "5m"
DEFAULT_TYPE = "avg"


@dataclass(frozen=True)
class RawAggregateRow:
    zone: str
    metric: str
    avg_value: float
    max_value: float


@dataclass(frozen=True)
class RawHourlyMaxRow:
    zone: str
    metric: str
    max_value: float


def fetch_latest_aggregated_value(
    zone: str,
    metric: str,
    *,
    aggregation_window: str = DEFAULT_WINDOW,
    aggregation_type: str = DEFAULT_TYPE,
) -> float | None:
    """
    Return the latest aggregate value for one zone + metric + aggregate kind.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT value
                FROM public.aggregated_data
                WHERE zone = %s
                  AND metric = %s
                  AND aggregation_window = %s
                  AND aggregation_type = %s
                ORDER BY window_end DESC
                LIMIT 1
                """,
                (zone, metric, aggregation_window, aggregation_type),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return float(row["value"])


def fetch_latest_row_per_zone_metric(
    *,
    aggregation_window: str = DEFAULT_WINDOW,
    aggregation_type: str = DEFAULT_TYPE,
) -> list[dict]:
    """
    Latest aggregate row for each (zone, metric) for the requested aggregate kind.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (zone, metric)
                    zone,
                    metric,
                    aggregation_window,
                    aggregation_type,
                    value,
                    window_start,
                    window_end
                FROM public.aggregated_data
                WHERE aggregation_window = %s
                  AND aggregation_type = %s
                ORDER BY zone, metric, window_end DESC
                """,
                (aggregation_window, aggregation_type),
            )
            return [dict(r) for r in cur.fetchall()]


def fetch_latest_row_per_metric_for_zone(
    zone: str,
    *,
    aggregation_window: str = DEFAULT_WINDOW,
    aggregation_type: str = DEFAULT_TYPE,
) -> list[dict]:
    """
    Latest aggregate row per metric for a single zone.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (metric)
                    zone,
                    metric,
                    aggregation_window,
                    aggregation_type,
                    value,
                    window_start,
                    window_end
                FROM public.aggregated_data
                WHERE zone = %s
                  AND aggregation_window = %s
                  AND aggregation_type = %s
                ORDER BY metric, window_end DESC
                """,
                (zone, aggregation_window, aggregation_type),
            )
            return [dict(r) for r in cur.fetchall()]


def fetch_history_for_zone_metric(
    zone: str,
    metric: str,
    *,
    limit: int,
    aggregation_window: str = DEFAULT_WINDOW,
    aggregation_type: str = DEFAULT_TYPE,
) -> list[dict]:
    """
    Newest-first aggregate history for a single zone + metric.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    zone,
                    metric,
                    aggregation_window,
                    aggregation_type,
                    value,
                    window_start,
                    window_end
                FROM public.aggregated_data
                WHERE zone = %s
                  AND metric = %s
                  AND aggregation_window = %s
                  AND aggregation_type = %s
                ORDER BY window_end DESC
                LIMIT %s
                """,
                (zone, metric, aggregation_window, aggregation_type, limit),
            )
            return [dict(r) for r in cur.fetchall()]


def fetch_five_minute_rollups(
    *, window_start: datetime, window_end: datetime
) -> list[RawAggregateRow]:
    """
    Compute avg + max per zone/metric from sensor_readings for one 5-minute window.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    zone,
                    metric_type AS metric,
                    AVG(value) AS avg_value,
                    MAX(value) AS max_value
                FROM public.sensor_readings
                WHERE timestamp >= %s
                  AND timestamp < %s
                GROUP BY zone, metric_type
                ORDER BY zone, metric_type
                """,
                (window_start, window_end),
            )
            rows = cur.fetchall()
    return [RawAggregateRow(**dict(r)) for r in rows]


def fetch_hourly_max_rollups(
    *, window_start: datetime, window_end: datetime
) -> list[RawHourlyMaxRow]:
    """
    Compute hourly maxima per zone/metric from the previous 5-minute max buckets.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    zone,
                    metric,
                    MAX(value) AS max_value
                FROM public.aggregated_data
                WHERE aggregation_window = '5m'
                  AND aggregation_type = 'max'
                  AND window_end > %s
                  AND window_end <= %s
                GROUP BY zone, metric
                ORDER BY zone, metric
                """,
                (window_start, window_end),
            )
            rows = cur.fetchall()
    return [RawHourlyMaxRow(**dict(r)) for r in rows]


def upsert_aggregate_row(
    *,
    zone: str,
    metric: str,
    aggregation_window: str,
    aggregation_type: str,
    value: float,
    window_start: datetime,
    window_end: datetime,
) -> None:
    """
    Insert or update one aggregate bucket so worker retries remain idempotent.
    """
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.aggregated_data (
                    zone,
                    metric,
                    aggregation_window,
                    aggregation_type,
                    value,
                    window_start,
                    window_end
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (
                    zone, metric, aggregation_window, aggregation_type, window_end
                )
                DO UPDATE
                SET value = EXCLUDED.value,
                    window_start = EXCLUDED.window_start
                """,
                (
                    zone,
                    metric,
                    aggregation_window,
                    aggregation_type,
                    value,
                    window_start,
                    window_end,
                ),
            )
        conn.commit()


def fetch_latest_bucket_end(
    *, aggregation_window: str, aggregation_type: str
) -> Optional[datetime]:
    """Return the most recent completed bucket end for one aggregate kind."""
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT MAX(window_end) AS window_end
                FROM public.aggregated_data
                WHERE aggregation_window = %s
                  AND aggregation_type = %s
                """,
                (aggregation_window, aggregation_type),
            )
            row = cur.fetchone()
    if not row or row["window_end"] is None:
        return None
    return row["window_end"]
