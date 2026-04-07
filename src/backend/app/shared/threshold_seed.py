"""
Idempotent startup seed for the three default thresholds.

These rows need to exist before the threshold evaluator worker can run
a meaningful evaluation cycle.  The seed only fires when the
`public.thresholds` table is completely empty, so it never overwrites
thresholds an operator has already configured.

Default thresholds:
    Zone A — AQI         > 150  (CRITICAL)
    Zone B — temperature > 35   (MEDIUM)
    Zone C — noise       > 85   (LOW)

Requires SUPABASE_DB_URL and migration 003_create_thresholds.sql applied.
If either is missing the seed is skipped and the app continues to start.
"""

from __future__ import annotations

import logging

from app.shared.db import get_supabase_db_url

logger = logging.getLogger(__name__)

# (zone, metric, condition, threshold_value, severity)
# severity strings must match the CHECK constraint in 003_create_thresholds.sql
_DEFAULT_THRESHOLDS = [
    ("Zone A", "aqi",         "gt", 150.0, "critical"),
    ("Zone B", "temperature", "gt",  35.0, "medium"),
    ("Zone C", "noise",       "gt",  85.0, "low"),
]


def seed_default_thresholds() -> None:
    """Insert the three default thresholds only when the table is empty."""
    db_url = get_supabase_db_url()
    if not db_url:
        logger.warning(
            "SUPABASE_DB_URL not set; skipping threshold seed "
            "(apply db/migrations/003_create_thresholds.sql when DB is ready)"
        )
        return

    try:
        import psycopg
    except ImportError:
        logger.warning("psycopg not installed; skipping threshold seed")
        return

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.thresholds")
                (count,) = cur.fetchone()

                if count > 0:
                    # Table already has data — never overwrite operator config.
                    logger.info(
                        "Threshold seed skipped — table already has %d row(s).", count
                    )
                    return

                cur.executemany(
                    """
                    INSERT INTO public.thresholds
                        (zone, metric, condition, threshold_value, severity, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    """,
                    _DEFAULT_THRESHOLDS,
                )
            conn.commit()

        logger.info(
            "Default threshold seed complete — inserted %d rows: "
            "Zone A AQI>150 CRITICAL, Zone B temp>35 MEDIUM, Zone C noise>85 LOW.",
            len(_DEFAULT_THRESHOLDS),
        )
    except Exception:
        logger.exception(
            "Default threshold seed failed (DB unreachable or migration not applied?); "
            "continuing without seed"
        )
