"""
Seed script: insert one ADMIN and one OPERATOR account on startup
Called from main.py lifespan with other seeds
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
    """Insert demo accounts if they do not already exist."""
    with db_connection() as conn:
        cursor = conn.cursor()
        for account in DEMO_ACCOUNTS:
            cursor.execute(
                "SELECT aid FROM accounts WHERE email = %s", (account["email"],)
            )
            if cursor.fetchone() is not None:
                continue  # already seeded
 
            password_hash = bcrypt.hashpw(
                account["password"].encode(), bcrypt.gensalt()
            ).decode()
 
            cursor.execute(
                """
                INSERT INTO accounts (name, email, password, clearance)
                VALUES (%s, %s, %s, %s)
                """,
                (account["name"], account["email"], password_hash, account["clearance"]),
            )
        conn.commit()
 