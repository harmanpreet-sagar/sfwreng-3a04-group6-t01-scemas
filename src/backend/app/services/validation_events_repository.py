"""Read latest values from `public.validation_events` (valid readings only)."""

from __future__ import annotations

from psycopg.rows import dict_row

from app.shared.db import db_connection
from app.shared.validation_event import VALIDATION_EVENTS_DB_STATUS_VALID


def fetch_latest_valid_raw_value(zone: str, metric: str) -> float | None:
    """
    Return `raw_value` from the newest validation event for this zone and metric
    whose status is VALID (non-anomalous, pipeline-accepted reading).

    `metric` matches `thresholds.metric` and `validation_events.metric_type`.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT raw_value
                FROM public.validation_events
                WHERE zone = %s
                  AND metric_type = %s
                  AND status = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (zone, metric, VALIDATION_EVENTS_DB_STATUS_VALID),
            )
            row = cur.fetchone()
    if row is None or row["raw_value"] is None:
        return None
    return float(row["raw_value"])
