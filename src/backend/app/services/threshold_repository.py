"""
Persistence helpers for `public.thresholds`.

This module is the only place in the codebase that runs SQL against the
thresholds table.  All callers (ThresholdService and the evaluator worker)
go through these functions so query changes need to be made in one place.

Two public interfaces are exposed:
  list_active_thresholds() — lightweight, used by the evaluator worker on a
                             tight polling loop; returns plain dataclasses.
  Full CRUD functions       — used by the Threshold Management API; return
                             Pydantic ThresholdResponse models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from psycopg.rows import dict_row

from app.shared.db import db_connection
from app.shared.threshold import ThresholdCreate, ThresholdResponse, ThresholdUpdate

# Single source of truth for which columns every SELECT returns.
# Keeping this constant in sync with the RETURNING clause means adding a column
# only requires one change here rather than updating every individual query.
_THRESHOLD_SELECT = (
    "id, zone, metric, condition, threshold_value, severity, "
    "is_active, created_at, updated_at"
)


# ── Lightweight type used by the threshold evaluator worker ───────────────────
# ActiveThresholdRow is a plain frozen dataclass rather than a ThresholdResponse
# Pydantic model because the evaluator runs every few seconds and does not need
# Pydantic's validation overhead for fields that will never be serialised to JSON.

@dataclass(frozen=True)
class ActiveThresholdRow:
    id: int
    zone: str
    metric: str
    condition: str
    threshold_value: float
    severity: str


def list_active_thresholds() -> list[ActiveThresholdRow]:
    """
    Return all thresholds where is_active = TRUE, ordered by id.

    Called by the threshold evaluator worker on every polling cycle.
    Returns cheap dataclasses instead of Pydantic models for performance.
    """
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


# ── Full CRUD for the Threshold Management API ────────────────────────────────

def insert_threshold(payload: ThresholdCreate) -> ThresholdResponse:
    """
    INSERT one threshold row and return it as a ThresholdResponse.

    Enum values are serialised to their string form (.value) because psycopg
    passes Python enums as their repr ("ThresholdCondition.gt") rather than
    their value ("gt"), which would fail the DB CHECK constraint.

    RETURNING is used instead of a follow-up SELECT so only one round-trip
    is needed and the newly assigned id/timestamps are captured atomically.
    """
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
    """Return every threshold row (active and inactive) ordered by id."""
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
    """
    Return the threshold with the given id, or None if it does not exist.

    Returning None (rather than raising) lets the service and router decide
    the appropriate HTTP response — usually a 404 from the router layer.
    """
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
    """
    Apply a partial update and return the updated row, or None if not found.

    Only the fields present in `changes` (not None) are included in the SET
    clause, so callers can send a single-field patch without accidentally
    clearing other columns.

    The `_id` key is used for the WHERE clause to avoid a name collision if
    a future schema change adds a column also named `id` to the UPDATE target.

    Enum values are converted to strings for the same reason as insert_threshold.
    """
    fields = changes.model_dump(exclude_none=True)
    # Skip the DB write when the caller sent an empty patch body; just return
    # the current state so the router can respond with 200.
    if not fields:
        return get_threshold_by_id(threshold_id)

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
    """
    Flip the is_active flag and return the updated row, or None if not found.

    `is_active` is keyword-only (the * forces it) to prevent accidental
    argument-order bugs like set_threshold_active(True, 5) silently updating
    the wrong row.
    """
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
    """
    DELETE the row and return True, or return False if the id did not exist.

    rowcount is checked instead of doing a prior SELECT to keep this to a
    single round-trip.  The caller (ThresholdService) uses the bool to decide
    whether to emit an audit event — no audit for a no-op delete.
    """
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.thresholds WHERE id = %s",
                (threshold_id,),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted
