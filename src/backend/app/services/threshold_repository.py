"""Persistence helpers for `public.thresholds`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from psycopg.rows import dict_row

from app.shared.db import db_connection
from app.shared.threshold import ThresholdCreate, ThresholdResponse, ThresholdUpdate

_THRESHOLD_SELECT = (
    "id, zone, metric, condition, threshold_value, severity, "
    "is_active, created_at, updated_at"
)


# ── Used internally by the threshold evaluator worker ──────────────────────────

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


# ── Full CRUD for the Threshold Management API ──────────────────────────────────

def insert_threshold(payload: ThresholdCreate) -> ThresholdResponse:
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                INSERT INTO public.thresholds
                    (zone, metric, condition, threshold_value, severity, is_active)
                VALUES
                    (%(zone)s, %(metric)s, %(condition)s, %(threshold_value)s,
                     %(severity)s, %(is_active)s)
                RETURNING {_THRESHOLD_SELECT}
                """,
                {
                    "zone": payload.zone,
                    "metric": payload.metric,
                    "condition": payload.condition.value,
                    "threshold_value": payload.threshold_value,
                    "severity": payload.severity.value,
                    "is_active": payload.is_active,
                },
            )
            row = cur.fetchone()
        conn.commit()
    return ThresholdResponse.model_validate(dict(row))


def list_thresholds() -> list[ThresholdResponse]:
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT {_THRESHOLD_SELECT}
                FROM public.thresholds
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return [ThresholdResponse.model_validate(dict(r)) for r in rows]


def get_threshold_by_id(threshold_id: int) -> Optional[ThresholdResponse]:
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT {_THRESHOLD_SELECT}
                FROM public.thresholds
                WHERE id = %s
                """,
                (threshold_id,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return ThresholdResponse.model_validate(dict(row))


def update_threshold(
    threshold_id: int, changes: ThresholdUpdate
) -> Optional[ThresholdResponse]:
    fields = changes.model_dump(exclude_none=True)
    if not fields:
        return get_threshold_by_id(threshold_id)

    # Serialize enum values to their DB string form
    if "condition" in fields:
        fields["condition"] = fields["condition"].value
    if "severity" in fields:
        fields["severity"] = fields["severity"].value

    set_clauses = ", ".join(f"{k} = %({k})s" for k in fields)
    fields["_id"] = threshold_id

    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                UPDATE public.thresholds
                SET {set_clauses}, updated_at = now()
                WHERE id = %(_id)s
                RETURNING {_THRESHOLD_SELECT}
                """,
                fields,
            )
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return ThresholdResponse.model_validate(dict(row))


def set_threshold_active(
    threshold_id: int, *, is_active: bool
) -> Optional[ThresholdResponse]:
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                UPDATE public.thresholds
                SET is_active = %s, updated_at = now()
                WHERE id = %s
                RETURNING {_THRESHOLD_SELECT}
                """,
                (is_active, threshold_id),
            )
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return ThresholdResponse.model_validate(dict(row))


def delete_threshold(threshold_id: int) -> bool:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.thresholds WHERE id = %s",
                (threshold_id,),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted
