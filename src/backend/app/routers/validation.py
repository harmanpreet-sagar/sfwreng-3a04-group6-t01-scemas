"""
Validation Router — REST API Endpoints

Exposes two endpoints for monitoring the health of the data ingestion pipeline:
- GET /validation/status: returns counts of valid, failed, and anomalous
  readings processed in the last hour. Used by the operational dashboard
  as a pipeline health indicator.
- GET /validation/events: returns the 50 most recent validation events
  with their status and reason. Accessible to OPERATOR and ADMIN roles.

Ported from asyncpg to psycopg so the project uses a single DB driver.
asyncpg used $1/$2 placeholders; psycopg uses %s.

Requires DB migration: db/migrations/005_create_validation_events.sql
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from psycopg.rows import dict_row

from app.shared.db import db_connection

router = APIRouter(prefix="/validation", tags=["Validation"])


@router.get("/status")
def validation_status() -> dict:
    """
    Return a count of each validation outcome for the last 60 minutes.

    The one-hour window is computed at request time so the result is always
    fresh — no caching layer is needed for this PoC.  Status values written
    by the pipeline are uppercase (VALID, FAILED, ANOMALY); the response
    normalises the keys to lowercase for consistency with the rest of the API.
    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM validation_events
                WHERE timestamp >= %s
                GROUP BY status
                """,
                (one_hour_ago,),
            )
            rows = cur.fetchall()

    # Build a lookup so missing statuses default to 0 instead of KeyError
    result = {row["status"]: row["count"] for row in rows}
    return {
        "valid":   result.get("VALID", 0),
        "failed":  result.get("FAILED", 0),
        "anomaly": result.get("ANOMALY", 0),
    }


@router.get("/events")
def validation_events() -> list:
    """
    Return the 50 most recent rows from validation_events, newest first.

    Limit of 50 is intentional for the PoC — add pagination parameters
    (offset/limit query params) before exposing this to a high-volume feed.
    The raw_value field contains the original sensor reading that was
    evaluated, which is useful when diagnosing FAILED or ANOMALY outcomes.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, sensor_id, zone, metric_type,
                       raw_value, status, reason, timestamp
                FROM validation_events
                ORDER BY timestamp DESC
                LIMIT 50
                """
            )
            rows = cur.fetchall()
    return [dict(row) for row in rows]