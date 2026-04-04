"""
Demo account seeding — called from main.py lifespan on every startup.

Why upsert instead of INSERT … IF NOT EXISTS?
  The first version used a plain INSERT with a conflict check that silently
  skipped rows that already existed. This caused a subtle bug: if the demo
  accounts were created in a previous run with a different password hash (e.g.
  by a manual INSERT or a bcrypt salt change), the skip meant the credentials
  in DEMO_ACCOUNTS no longer matched what was stored in the DB. The result was
  a login error even though the account existed and was active.

  The ON CONFLICT (email) DO UPDATE strategy ensures that on every startup the
  stored hash is always derived from the plaintext password in DEMO_ACCOUNTS.
  This guarantees that demo credentials are always valid after a fresh `docker
  compose up`, regardless of what the database contained before.

  is_active is also reset to TRUE so that a previously deactivated demo account
  is restored automatically — useful for demo resets without manual DB surgery.

Security note:
  bcrypt.gensalt() generates a new salt on every run, so the hash stored in
  the DB changes on every startup. This is safe because bcrypt.checkpw() in
  AccountService.login() compares the plaintext against the stored hash, not
  hash-to-hash. The changing hash does not cause login failures.
"""

from __future__ import annotations

import bcrypt
from app.shared.db import db_connection


DEMO_ACCOUNTS = [
    {
        "name":      "Demo Admin",
        "email":     "admin@demo.com",
        "password":  "admin123",
        "clearance": "admin",
    },
    {
        "name":      "Demo Operator",
        "email":     "operator@demo.com",
        "password":  "operator123",
        "clearance": "operator",
    },
]


def seed_demo_accounts() -> None:
    """
    Upsert demo accounts on every startup.

    ON CONFLICT DO UPDATE ensures the password is always reset to the value
    defined in DEMO_ACCOUNTS, so a stale hash from a previous run never locks
    out the demo. is_active is also reset to TRUE to handle cases where an
    account was deactivated during a previous demo session.
    """
    with db_connection() as conn:
        cursor = conn.cursor()
        for account in DEMO_ACCOUNTS:
            # Hash is re-generated on every startup (new salt each time).
            # bcrypt.checkpw in the login flow handles the comparison correctly.
            password_hash = bcrypt.hashpw(
                account["password"].encode(), bcrypt.gensalt()
            ).decode()
            cursor.execute(
                """
                INSERT INTO accounts (name, email, password, clearance)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE
                    SET password  = EXCLUDED.password,
                        clearance = EXCLUDED.clearance,
                        is_active = TRUE
                """,
                (account["name"], account["email"], password_hash, account["clearance"]),
            )
        conn.commit()
