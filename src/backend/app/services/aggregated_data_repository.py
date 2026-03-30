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
