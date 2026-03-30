"""Read latest aggregated values from `public.aggregated_data`."""

from __future__ import annotations

from psycopg.rows import dict_row

from app.shared.db import db_connection


def fetch_latest_aggregated_value(zone: str, metric: str) -> float | None:
    """
    Return the aggregated `value` for the row with the latest `window_end`
    for this zone + metric, or None if no data exists.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT value
                FROM public.aggregated_data
                WHERE zone = %s AND metric = %s
                ORDER BY window_end DESC
                LIMIT 1
                """,
                (zone, metric),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return float(row["value"])


def fetch_latest_row_per_zone_metric() -> list[dict]:
    """
    Latest aggregated row for each (zone, metric), using the greatest window_end.

    Uses PostgreSQL DISTINCT ON (matches evaluator semantics for “current” values).
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (zone, metric)
                    zone,
                    metric,
                    value,
                    window_end
                FROM public.aggregated_data
                ORDER BY zone, metric, window_end DESC
                """
            )
            return [dict(r) for r in cur.fetchall()]
