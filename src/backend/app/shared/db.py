"""Lightweight Postgres access for services (same connection string as migrations/seeds)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg


def get_supabase_db_url() -> str | None:
    url = os.getenv("SUPABASE_DB_URL", "").strip()
    return url or None


@contextmanager
def db_connection() -> Generator[psycopg.Connection, None, None]:
    url = get_supabase_db_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not set")
    with psycopg.connect(url) as conn:
        yield conn
