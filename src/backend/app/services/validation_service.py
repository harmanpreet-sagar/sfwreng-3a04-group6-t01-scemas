"""
Validation Pipeline

This is where the core logic is contained for the pipeline. The process_message() function is the most important one as it is called
in the mqtt_subscriber file, which is where the json data is parsed. 

Processes incoming sensor readings through three sequential steps:
1. EnsureMQTTCompliance: validates required fields, correct types, and
   value within the defined range for the given metric type. Failed readings
   are logged to validation_events with status FAILED and dropped.

   How the code works: 
   - First it calls the function ensure_mqtt_compliance (returns either true or false). This function checks if the data
     contains the required fields (sensorid, zone, metric, value, time). If it doesn't then it returns false.
     Also checks if value is a number and if metric is valid. 
     IF this function returns false, then in process_message() then we call the function "write_validation_events" 
     which writes to the table in supabase with the label "Failed"

2. SensorMonitor: compares the incoming value against the last 10 readings
   for that sensor and metric. Flags as ANOMALY if the value deviates more
   than 3 standard deviations from the mean. Anomalous readings are logged
   but still stored.

   How the code works:
   - calls the sensor_monitor function which uses the last 10 readings to find mean and standard deviation and if the 
   value we are comparing deviates more than 3 standard deviation from mean, it flags it as anomaly. If it's fine it returns true. 

   3. StoreValidatedData: inserts valid readings into the sensor_readings table
   in Supabase for downstream aggregation and alerting.
   In the code it simply uses a Query to store the data in the sensor_readings table. Also writes to validation_events table 
   stating that data is VALID. 




import os
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev

Ported from asyncpg to psycopg so only one DB driver is needed across the
whole project and asyncpg does not have to appear in requirements.txt.

process_message() is now synchronous; the paho on_message callback can call
it directly without asyncio.run().

Pipeline stages
    1. EnsureMQTTCompliance  — required fields + value-range check
    2. SensorMonitor         — 3-sigma anomaly detection against last 10 readings
    3. StoreValidatedData    — INSERT into sensor_readings
    4. WriteValidationEvent  — INSERT outcome into validation_events

Requires DB migrations:
    db/migrations/005_create_validation_events.sql
    db/migrations/006_create_sensor_readings.sql
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Optional, Tuple

from psycopg.rows import dict_row

from app.shared.db import db_connection

logger = logging.getLogger(__name__)

# Physically possible ranges for each metric type.
# Readings outside these bounds are hard-rejected as FAILED before any DB work.
VALID_RANGES: dict[str, Tuple[float, float]] = {
    "aqi":         (0, 500),
    "temperature": (-30, 50),
    "humidity":    (0, 100),
    "noise":       (0, 140),
}

# Every sensor message must carry these keys or it is rejected immediately.
REQUIRED_FIELDS = ["sensorId", "zone", "metricType", "value", "timestamp"]


# ── Stage 1: MQTT compliance check ────────────────────────────────────────────

def ensure_mqtt_compliance(payload: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate the structure and value of an incoming sensor payload.

    This runs before any DB access so malformed messages are caught cheaply.
    Returns (True, None) on success or (False, reason_string) on failure.
    """
    for field in REQUIRED_FIELDS:
        if field not in payload:
            return False, f"Missing required field: {field}"

    if not isinstance(payload["value"], (int, float)):
        return False, "value must be a number"

    metric = payload["metricType"]
    if metric not in VALID_RANGES:
        return False, f"Unknown metric type: {metric}"

    low, high = VALID_RANGES[metric]
    if not (low <= payload["value"] <= high):
        return False, f"{metric} value {payload['value']} out of range [{low}, {high}]"

    return True, None


# ── Stage 2: Anomaly detection ────────────────────────────────────────────────

def sensor_monitor(conn, payload: dict) -> Tuple[bool, Optional[str]]:
    """
    Apply the 3-sigma rule against the last 10 readings for this sensor/metric.

    A reading is flagged ANOMALY when it deviates more than 3 standard
    deviations from the rolling mean.  Fewer than 3 historical readings means
    not enough baseline exists, so the reading is treated as normal.

    std == 0 (all identical historical values) is also treated as normal to
    avoid division-by-zero and false positives from sensors that report a
    constant value for extended periods.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT value FROM sensor_readings
            WHERE sensor_id = %s AND metric_type = %s
            ORDER BY timestamp DESC
            LIMIT 10
            """,
            (payload["sensorId"], payload["metricType"]),
        )
        rows = cur.fetchall()

    values = [r["value"] for r in rows]
    if len(values) < 3:
        return False, None

    avg = mean(values)
    std = stdev(values)
    if std == 0:
        return False, None

    if abs(payload["value"] - avg) > 3 * std:
        return (
            True,
            f"Anomaly: value {payload['value']} deviates >3σ from mean {avg:.2f}",
        )
    return False, None


# ── Stage 3: Persist reading ──────────────────────────────────────────────────

def store_validated_data(conn, payload: dict) -> None:
    """
    INSERT the reading into sensor_readings regardless of anomaly status.

    Anomalous readings are still stored so the anomaly detection in stage 2
    has a complete history to compare against in future messages.  The
    validation_events table (stage 4) records whether this reading was anomalous.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sensor_readings (sensor_id, zone, metric_type, value, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                payload["sensorId"],
                payload["zone"],
                payload["metricType"],
                float(payload["value"]),
                datetime.now(timezone.utc),
            ),
        )


# ── Stage 4: Record outcome ───────────────────────────────────────────────────

def write_validation_event(
    conn, payload: dict, *, status: str, reason: Optional[str]
) -> None:
    """
    Append one row to validation_events recording the pipeline outcome.

    status is one of: VALID, FAILED, ANOMALY.
    reason is None for VALID outcomes and a human-readable string for the other two.
    payload.get() with defaults is used for FAILED events where fields may be
    missing (the compliance check already caught that they were absent).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO validation_events
                (sensor_id, zone, metric_type, raw_value, status, reason, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload.get("sensorId", "unknown"),
                payload.get("zone"),
                payload.get("metricType"),
                float(payload["value"]) if "value" in payload else None,
                status,
                reason,
                datetime.now(timezone.utc),
            ),
        )


# ── Public entry point ────────────────────────────────────────────────────────

def process_message(payload: dict) -> None:
    """
    Run the full four-stage validation pipeline for one incoming MQTT message.

    A single DB connection is opened for the entire pipeline so all four
    writes (sensor_readings + validation_events) land in the same transaction.
    conn.commit() at the end means either everything is persisted or nothing
    is — there is no partial state left in the DB if an exception is raised.

    Synchronous — call directly from paho's on_message without asyncio.run().
    """
    try:
        with db_connection() as conn:
            # Stage 1: reject structurally invalid or out-of-range messages early
            valid, reason = ensure_mqtt_compliance(payload)
            if not valid:
                write_validation_event(conn, payload, status="FAILED", reason=reason)
                conn.commit()
                return

            # Stage 2: statistical anomaly check against sensor history
            anomaly, reason = sensor_monitor(conn, payload)
            if anomaly:
                # Record the anomaly outcome before storing the reading so the
                # validation_events row references the same timestamp window.
                write_validation_event(conn, payload, status="ANOMALY", reason=reason)

            # Stage 3: persist the reading (even if anomalous — needed for future history)
            store_validated_data(conn, payload)

            # Stage 4: record VALID only if no anomaly was detected
            if not anomaly:
                write_validation_event(conn, payload, status="VALID", reason=None)

            conn.commit()
    except Exception:
        logger.exception("Validation pipeline error for payload: %s", payload)
