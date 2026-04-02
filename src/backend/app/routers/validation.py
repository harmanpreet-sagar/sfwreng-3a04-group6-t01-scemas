from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
import asyncpg
import os

router = APIRouter(prefix="/validation", tags=["validation"])

DB_URL = os.getenv("SUPABASE_DB_URL")


async def get_db():
    return await asyncpg.connect(DB_URL)


@router.get("/status")
async def validation_status():
    """Return count of valid vs failed readings in the last hour."""
    conn = await get_db()
    try:
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        rows = await conn.fetch(
            """
            SELECT status, COUNT(*) as count
            FROM validation_events
            WHERE timestamp >= $1
            GROUP BY status
            """,
            one_hour_ago,
        )
        result = {row["status"]: row["count"] for row in rows}
        return {
            "valid": result.get("VALID", 0),
            "failed": result.get("FAILED", 0),
            "anomaly": result.get("ANOMALY", 0),
        }
    finally:
        await conn.close()


@router.get("/events")
async def validation_events():
    """Return recent validation events."""
    conn = await get_db()
    try:
        rows = await conn.fetch(
            """
            SELECT id, sensor_id, zone, metric_type, raw_value, status, reason, timestamp
            FROM validation_events
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()