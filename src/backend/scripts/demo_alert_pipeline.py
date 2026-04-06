#!/usr/bin/env python3
"""
Simple explanation: A one-shot “show and tell” that fakes data, runs the checker once,
and walks through saving an alert, optional text message, and live push—like pressing
demo on a toy.

End-to-end alerts demo (one evaluator cycle):

  validation_events (VALID) + thresholds → run_threshold_evaluation_cycle()
  → AlertService.create_alert → DB insert → audit log → Twilio (if CRITICAL + env set) → SSE publish

Uses isolated zone/metric pipedemo/co2 so your existing demo rows are untouched.

Run from src/backend:

  PYTHONPATH=. python scripts/demo_alert_pipeline.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_dir))

from dotenv import load_dotenv

load_dotenv(_backend_dir.parent / ".env")
load_dotenv(_backend_dir / ".env")

ZONE = "pipedemo"
METRIC = "co2"


def main() -> int:
    db_url = (os.getenv("SUPABASE_DB_URL") or "").strip()
    if not db_url:
        print("SUPABASE_DB_URL is not set.", file=sys.stderr)
        return 1

    import psycopg

    print("1) Seed DB: latest VALID validation event + active CRITICAL threshold (breached)")
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.alerts WHERE zone = %s AND metric = %s",
                (ZONE, METRIC),
            )
            cur.execute(
                "DELETE FROM public.thresholds WHERE zone = %s AND metric = %s",
                (ZONE, METRIC),
            )
            cur.execute(
                "DELETE FROM public.validation_events WHERE zone = %s AND metric_type = %s",
                (ZONE, METRIC),
            )
            cur.execute(
                """
                INSERT INTO public.validation_events
                    (sensor_id, zone, metric_type, raw_value, status, reason, timestamp)
                VALUES (%s, %s, %s, %s, 'VALID', NULL, now())
                """,
                (f"pipedemo-{METRIC}", ZONE, METRIC, 900.0),
            )
            cur.execute(
                """
                INSERT INTO public.thresholds
                    (zone, metric, condition, threshold_value, severity, is_active)
                VALUES (%s, %s, 'gt', %s, 'critical', true)
                """,
                (ZONE, METRIC, 400.0),
            )
        conn.commit()
    print(f"   → {ZONE}/{METRIC}: observed 900, rule gt 400, severity=critical")

    print("2) Run one threshold evaluation cycle (same as background worker, once)")
    from app.services.threshold_evaluation import run_threshold_evaluation_cycle

    run_threshold_evaluation_cycle()

    print("3) Read back newest alert row")
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, zone, metric, severity, status, threshold_id
                FROM public.alerts
                WHERE zone = %s AND metric = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (ZONE, METRIC),
            )
            row = cur.fetchone()

    if not row:
        print("   No alert inserted — check logs and DB connectivity.", file=sys.stderr)
        return 2

    cols = ["id", "zone", "metric", "severity", "status", "threshold_id"]
    print("   ", dict(zip(cols, row)))

    print("4) Side effects (already ran inside create_alert if insert succeeded):")
    print("   • Audit: event_type alert.created (logger scemas.audit)")
    print("   • Twilio: SMS to TWILIO_TO_NUMBER if env complete (see server/script logs)")
    print("   • SSE: publish_alert_sse (visible on GET /alerts/stream if clients connected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
