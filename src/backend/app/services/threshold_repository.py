"""Read active threshold rules from `public.thresholds`."""

from __future__ import annotations

from dataclasses import dataclass

from psycopg.rows import dict_row

from app.shared.db import db_connection


@dataclass(frozen=True)
class ActiveThresholdRow:
    id: int
    zone: str
    metric: str
    condition: str
    threshold_value: float
    severity: str


def list_active_thresholds() -> list[ActiveThresholdRow]:
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, zone, metric, condition, threshold_value, severity
                FROM public.thresholds
                WHERE is_active = TRUE
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return [ActiveThresholdRow(**dict(r)) for r in rows]
