"""Persistence helpers for `public.alerts` (no HTTP layer)."""

from __future__ import annotations

from typing import Optional

from psycopg.rows import dict_row

from app.models.alert import AlertCreate, AlertResponse, AlertSeverity, AlertStatus
from app.shared.db import db_connection


def active_alert_exists_for_zone_metric(zone: str, metric: str) -> bool:
    """Return True if an alert with status `active` already exists for this zone + metric."""
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM public.alerts
                WHERE zone = %s AND metric = %s AND status = %s
                LIMIT 1
                """,
                (zone, metric, AlertStatus.active.value),
            )
            return cur.fetchone() is not None


def try_insert_active_alert(payload: AlertCreate) -> Optional[AlertResponse]:
    """
    Insert a new active alert. Returns None if a duplicate active (zone, metric) exists.

    Relies on partial unique index uq_alerts_active_zone_metric and ON CONFLICT DO NOTHING.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO public.alerts (
                    zone, metric, severity, message, status,
                    observed_value, threshold_value, threshold_id
                )
                VALUES (
                    %(zone)s, %(metric)s, %(severity)s, %(message)s, %(status)s,
                    %(observed_value)s, %(threshold_value)s, %(threshold_id)s
                )
                ON CONFLICT (zone, metric) WHERE (status = 'active') DO NOTHING
                RETURNING
                    id, zone, metric, severity, message, status,
                    observed_value, threshold_value, threshold_id,
                    created_at, updated_at, acknowledged_at, resolved_at
                """,
                {
                    "zone": payload.zone,
                    "metric": payload.metric,
                    "severity": payload.severity.value,
                    "message": payload.message,
                    "status": AlertStatus.active.value,
                    "observed_value": payload.observed_value,
                    "threshold_value": payload.threshold_value,
                    "threshold_id": payload.threshold_id,
                },
            )
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return AlertResponse.model_validate(dict(row))


_ALERT_SELECT_LIST = (
    "id, zone, metric, severity, message, status, "
    "observed_value, threshold_value, threshold_id, "
    "created_at, updated_at, acknowledged_at, resolved_at"
)


def list_alerts(
    *,
    status: Optional[AlertStatus] = None,
    zone: Optional[str] = None,
    severity: Optional[AlertSeverity] = None,
) -> list[AlertResponse]:
    """Return alerts matching optional filters, newest first (`created_at DESC`)."""
    conditions: list[str] = []
    params: list[object] = []
    if status is not None:
        conditions.append("status = %s")
        params.append(status.value)
    if zone is not None:
        conditions.append("zone = %s")
        params.append(zone)
    if severity is not None:
        conditions.append("severity = %s")
        params.append(severity.value)

    where_sql = " AND ".join(conditions) if conditions else "TRUE"
    query = f"""
        SELECT {_ALERT_SELECT_LIST}
        FROM public.alerts
        WHERE {where_sql}
        ORDER BY created_at DESC
    """

    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [AlertResponse.model_validate(dict(r)) for r in rows]


def get_alert_by_id(alert_id: int) -> Optional[AlertResponse]:
    """Return one alert by primary key, or None if missing."""
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT {_ALERT_SELECT_LIST}
                FROM public.alerts
                WHERE id = %s
                """,
                (alert_id,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return AlertResponse.model_validate(dict(row))


def try_acknowledge_active_alert(alert_id: int) -> Optional[AlertResponse]:
    """
    Transition active -> acknowledged. Returns updated row, or None if no matching row
    (missing id or not active).
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                UPDATE public.alerts
                SET
                    status = %s,
                    acknowledged_at = now(),
                    updated_at = now()
                WHERE id = %s AND status = %s
                RETURNING {_ALERT_SELECT_LIST}
                """,
                (AlertStatus.acknowledged.value, alert_id, AlertStatus.active.value),
            )
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return AlertResponse.model_validate(dict(row))


def try_resolve_alert(alert_id: int) -> Optional[AlertResponse]:
    """
    Transition active or acknowledged -> resolved. Returns updated row, or None if
    no matching row (missing id or already resolved).
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                UPDATE public.alerts
                SET
                    status = %s,
                    resolved_at = now(),
                    updated_at = now()
                WHERE id = %s AND status IN (%s, %s)
                RETURNING {_ALERT_SELECT_LIST}
                """,
                (
                    AlertStatus.resolved.value,
                    alert_id,
                    AlertStatus.active.value,
                    AlertStatus.acknowledged.value,
                ),
            )
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return AlertResponse.model_validate(dict(row))
