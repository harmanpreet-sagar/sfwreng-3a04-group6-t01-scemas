from __future__ import annotations
 
from datetime import datetime
from typing import List, Optional
 
import bcrypt
 
from app.shared.db import db_connection
from app.shared.account import AccountCreate, AccountResponse, AuditLogEntry
 
 
def _row_to_account(row: tuple) -> AccountResponse:
    return AccountResponse(
        aid=row[0], name=row[1], email=row[2],
        clearance=row[3], is_active=row[4],
        created_at=row[5], updated_at=row[6],
    )
 
 
def _write_audit_log(cursor, event_type, actor_id=None, actor_email=None,target_id=None, target_email=None, detail=None):
    cursor.execute(
        """
        INSERT INTO audit_log
            (event_type, actor_id, actor_email, target_id, target_email, detail)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (event_type, actor_id, actor_email, target_id, target_email, detail),
    )
 
