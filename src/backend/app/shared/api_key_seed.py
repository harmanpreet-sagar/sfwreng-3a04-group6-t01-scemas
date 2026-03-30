"""
Idempotent startup seed for the demo public API key.

The raw key is never stored in the database—only a SHA-256 hex digest (key_hash).

Configuration:
- DEMO_PUBLIC_API_KEY: optional. If set (non-empty), that value is the demo key
  clients send in headers later. If unset, a fixed development default is used
  (see DEFAULT_DEMO_PUBLIC_API_KEY below) so local/demo runs work without .env.

Requires SUPABASE_DB_URL and migration 002_create_api_keys.sql applied.
If SUPABASE_DB_URL is missing or the DB is unreachable, seeding is skipped and
the app still starts.
"""

from __future__ import annotations

import hashlib
import logging
import os

from app.shared.db import get_supabase_db_url

logger = logging.getLogger(__name__)

# Fixed PoC default when DEMO_PUBLIC_API_KEY is not set (document in .env.example).
DEFAULT_DEMO_PUBLIC_API_KEY = "scemas-demo-public-api-key"

DEMO_KEY_LABEL = "SCEMAS Demo Public API"


def _demo_key_plaintext() -> str:
    raw = os.getenv("DEMO_PUBLIC_API_KEY", "").strip()
    return raw if raw else DEFAULT_DEMO_PUBLIC_API_KEY


def _key_hash(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def seed_demo_public_api_key() -> None:
    """Insert one demo API key row if missing (same key_hash => no duplicate)."""
    db_url = get_supabase_db_url()
    if not db_url:
        logger.warning(
            "SUPABASE_DB_URL not set; skipping demo API key seed "
            "(apply db/migrations/002_create_api_keys.sql when DB is ready)"
        )
        return

    try:
        import psycopg
    except ImportError:
        logger.warning("psycopg not installed; skipping demo API key seed")
        return

    plaintext = _demo_key_plaintext()
    digest = _key_hash(plaintext)

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.api_keys (key_hash, label, is_active)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (key_hash) DO NOTHING
                    """,
                    (digest, DEMO_KEY_LABEL),
                )
            conn.commit()
        logger.info(
            "Demo public API key seed finished (idempotent, label=%r). "
            "Set DEMO_PUBLIC_API_KEY to use a custom demo key.",
            DEMO_KEY_LABEL,
        )
    except Exception:
        logger.exception(
            "Demo API key seed failed (DB unreachable or migration not applied?); "
            "continuing without seed"
        )
