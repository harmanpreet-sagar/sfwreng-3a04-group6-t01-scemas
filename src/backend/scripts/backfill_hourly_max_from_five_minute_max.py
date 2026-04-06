"""Backfill 1h max aggregate rows from existing 5m max buckets.

Usage:
    cd src/backend
    python3 scripts/backfill_hourly_max_from_five_minute_max.py

This script does not require a schema migration. It recomputes hourly maxima
purely from rows already present in public.aggregated_data where:
  aggregation_window = '5m'
  aggregation_type   = 'max'
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def load_local_env() -> None:
    env_path = SRC_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    load_local_env()
    db_url = os.getenv("SUPABASE_DB_URL", "").strip()
    if not db_url:
        print("SUPABASE_DB_URL is not set", file=sys.stderr)
        return 1

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                WITH hourly_rollups AS (
                    SELECT
                        zone,
                        metric,
                        MAX(value) AS max_value,
                        date_trunc('hour', window_end - interval '1 minute') AS window_start,
                        date_trunc('hour', window_end - interval '1 minute') + interval '1 hour' AS window_end
                    FROM public.aggregated_data
                    WHERE aggregation_window = '5m'
                      AND aggregation_type = 'max'
                    GROUP BY
                        zone,
                        metric,
                        date_trunc('hour', window_end - interval '1 minute')
                )
                INSERT INTO public.aggregated_data (
                    zone,
                    metric,
                    aggregation_window,
                    aggregation_type,
                    value,
                    window_start,
                    window_end
                )
                SELECT
                    zone,
                    metric,
                    '1h',
                    'max',
                    max_value,
                    window_start,
                    window_end
                FROM hourly_rollups
                ON CONFLICT (zone, metric, aggregation_window, aggregation_type, window_end)
                DO UPDATE
                SET value = EXCLUDED.value,
                    window_start = EXCLUDED.window_start
                RETURNING zone, metric, value, window_start, window_end
                """
            )
            rows = cur.fetchall()
        conn.commit()

    print(f"Backfilled {len(rows)} hourly max rows from 5m max buckets.")
    for row in rows[:10]:
        print(
            f"{row['zone']} | {row['metric']} | {row['value']:.2f} | "
            f"{row['window_start']} -> {row['window_end']}"
        )
    if len(rows) > 10:
        print(f"... and {len(rows) - 10} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
