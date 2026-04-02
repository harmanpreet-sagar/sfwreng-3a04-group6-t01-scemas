"""Persistence helpers for `public.thresholds`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from psycopg.rows import dict_row

from app.shared.db import db_connection
from app.shared.threshold import ThresholdCreate, ThresholdResponse, ThresholdUpdate

# Single source of truth for which columns every SELECT returns.
# Keeping this in sync with the RETURNING clause means adding a column
# only requires one change here rather than touching every query.
_THRESHOLD_SELECT = (
    "id, zone, metric, condition, threshold_value, severity, "
    "is_active, created_at, updated_at"
)


# ── Used internally by the threshold evaluator worker ──────────────────────────
# ActiveThresholdRow is a plain dataclass instead of ThresholdResponse
# because the evaluator runs every 5 seconds and doesn't need Pydantic
# validation overhead on fields it will never expose over HTTP.

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
    # Enum values are serialized to their string form (.value) because psycopg
    # sends Python enums as their repr, not their value, which would fail the
    # DB CHECK constraint.
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
    # No-op update: skip the round-trip write but still return the current row
    # so the router can respond with 200 rather than 404.
    if not fields:
        return get_threshold_by_id(threshold_id)

    # Enum values must be strings for the DB CHECK constraint (same reason as insert).
    if "condition" in fields:
        fields["condition"] = fields["condition"].value
    if "severity" in fields:
        fields["severity"] = fields["severity"].value

    set_clauses = ", ".join(f"{k} = %({k})s" for k in fields)
    # Use `_id` as the WHERE parameter key to avoid collision with any column
    # named `id` that might appear in the SET clause in future.
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
    threshold_id: int, *, is_active: bool  # keyword-only to prevent arg-order mistakes
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
            # rowcount is the only way to tell whether the DELETE matched a row
            # without a prior SELECT, keeping this to a single round-trip.
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted
