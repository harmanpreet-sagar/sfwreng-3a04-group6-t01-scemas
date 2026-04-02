import os
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev

import asyncpg

DB_URL = os.getenv("SUPABASE_DB_URL")

VALID_RANGES = {
    "aqi": (0, 500),
    "temperature": (-30, 50),
    "humidity": (0, 100),
    "noise": (0, 140),
}

REQUIRED_FIELDS = ["sensorId", "zone", "metricType", "value", "timestamp"]


async def get_db():
    return await asyncpg.connect(DB_URL)


async def process_message(payload: dict):
    conn = await get_db()
    try:
        # Step 1 - EnsureMQTTCompliance
        valid, reason = ensure_mqtt_compliance(payload)
        if not valid:
            await write_validation_event(conn, payload, status="FAILED", reason=reason)
            return

        # Step 2 - SensorMonitor (anomaly detection)
        anomaly, reason = await sensor_monitor(conn, payload)
        if anomaly:
            await write_validation_event(conn, payload, status="ANOMALY", reason=reason)
            # Still store the reading even if anomalous

        # Step 3 - StoreValidatedData
        await store_validated_data(conn, payload)

        if not anomaly:
            await write_validation_event(conn, payload, status="VALID", reason=None)

    except Exception as e:
        print(f"❌ Validation pipeline error: {e}")
    finally:
        await conn.close()


def ensure_mqtt_compliance(payload: dict):
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in payload:
            return False, f"Missing required field: {field}"

    # Check types
    if not isinstance(payload["value"], (int, float)):
        return False, "value must be a number"

    # Check valid range
    metric = payload["metricType"]
    if metric not in VALID_RANGES:
        return False, f"Unknown metric type: {metric}"

    low, high = VALID_RANGES[metric]
    if not (low <= payload["value"] <= high):
        return False, f"{metric} value {payload['value']} out of range [{low}, {high}]"

    return True, None


async def sensor_monitor(conn, payload: dict):
    rows = await conn.fetch(
        """
        SELECT value FROM sensor_readings
        WHERE sensor_id = $1 AND metric_type = $2
        ORDER BY timestamp DESC LIMIT 10
        """,
        payload["sensorId"],
        payload["metricType"],
    )

    values = [r["value"] for r in rows]

    if len(values) < 3:
        return False, None  # Not enough history to detect anomaly

    avg = mean(values)
    std = stdev(values)

    if std == 0:
        return False, None

    if abs(payload["value"] - avg) > 3 * std:
        return True, f"Anomaly detected: value {payload['value']} deviates more than 3 std devs from mean {avg:.2f}"

    return False, None


async def store_validated_data(conn, payload: dict):
    await conn.execute(
        """
        INSERT INTO sensor_readings (sensor_id, zone, metric_type, value, timestamp)
        VALUES ($1, $2, $3, $4, $5)
        """,
        payload["sensorId"],
        payload["zone"],
        payload["metricType"],
        float(payload["value"]),
        datetime.now(timezone.utc),
    )


async def write_validation_event(conn, payload: dict, status: str, reason: str):
    await conn.execute(
        """
        INSERT INTO validation_events (sensor_id, zone, metric_type, raw_value, status, reason, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        payload.get("sensorId", "unknown"),
        payload.get("zone"),
        payload.get("metricType"),
        float(payload["value"]) if "value" in payload else None,
        status,
        reason,
        datetime.now(timezone.utc),
    )