"""Lookup helpers for `public.api_keys` (no HTTP layer)."""

from __future__ import annotations

from typing import Optional

from psycopg.rows import dict_row

from app.shared.db import db_connection


def fetch_active_api_key_by_hash(key_hash: str) -> Optional[dict]:
    """
    Return id and label for an active key with the given hash, or None if missing/inactive.
    """
    with db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, label
                FROM public.api_keys
                WHERE key_hash = %s AND is_active = TRUE
                LIMIT 1
                """,
                (key_hash,),
            )
            row = cur.fetchone()
    return dict(row) if row else None
