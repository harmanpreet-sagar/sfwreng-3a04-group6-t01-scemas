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
 

class AccountService:
 
    @staticmethod
    def login(email: str, password: str) -> Optional[dict]:
        """
        Logins controller: checkAccountExists() + tryPassword()
        """
        print(f"[AUTH] Checking account existence for: {email}")
 
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT aid, name, email, clearance, is_active, created_at, updated_at, password FROM accounts WHERE email = %s",
                (email,),
            )
            row = cursor.fetchone()
 
            if row is None or not row[4]:
                print(f"[AUTH] Login failed — account not found or inactive: {email}")
                _write_audit_log(cursor, "login_failure", actor_email=email, detail="Account not found or inactive")
                conn.commit()
                return None
 
            aid = row[0]
            password_hash = row[7]
 
            print(f"[AUTH] Verifying password for aid={aid} (POC: bcrypt check)")
            if not bcrypt.checkpw(password.encode(), password_hash.encode()):
                print(f"[AUTH] Login failed — incorrect password for: {email}")
                _write_audit_log(cursor, "login_failure", actor_id=aid, actor_email=email, detail="Incorrect password")
                conn.commit()
                return None
 
            print(f"[AUTH] Identity verified — login successful for aid={aid}")
            _write_audit_log(cursor, "login_success", actor_id=aid, actor_email=email)
            conn.commit()
 
        return {"account": _row_to_account(row[:7])}
 
    @staticmethod
    def list_accounts() -> List[AccountResponse]:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT aid, name, email, clearance, is_active, created_at, updated_at FROM accounts ORDER BY aid"
            )
            return [_row_to_account(r) for r in cursor.fetchall()]
 
    @staticmethod
    def get_account_by_id(aid: int) -> Optional[AccountResponse]:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT aid, name, email, clearance, is_active, created_at, updated_at FROM accounts WHERE aid = %s",
                (aid,),
            )
            row = cursor.fetchone()
        return _row_to_account(row) if row else None
 
    @staticmethod
    def create_account(data: AccountCreate, actor_id: int, actor_email: str) -> AccountResponse:
        """Logins.createAccount() -> AccountDB.create(). Logs account_created."""
        print(f"[AUTH] Admin clearance confirmed for account creation (POC stub) — actor aid={actor_id}")
        password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO accounts (name, email, password, clearance)
                VALUES (%s, %s, %s, %s)
                RETURNING aid, name, email, clearance, is_active, created_at, updated_at
                """,
                (data.name, data.email, password_hash, data.clearance),
            )
            row = cursor.fetchone()
            _write_audit_log(cursor, "account_created", actor_id=actor_id,actor_email=actor_email, target_id=row[0], target_email=data.email)
            conn.commit()
        return _row_to_account(row)
 
    @staticmethod
    def change_credentials(aid: int, new_password: str, actor_id: int, actor_email: str) -> Optional[AccountResponse]:
        """Logs password_changed."""
        print(f"[AUTH] Identity verified for credential change (POC stub) — actor aid={actor_id}, target aid={aid}")
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE accounts SET password = %s, updated_at = NOW()
                WHERE aid = %s
                RETURNING aid, name, email, clearance, is_active, created_at, updated_at
                """,
                (password_hash, aid),
            )
            row = cursor.fetchone()
            if row:
                _write_audit_log(cursor, "password_changed", actor_id=actor_id, actor_email=actor_email, target_id=aid, target_email=row[2])
            conn.commit()
        return _row_to_account(row) if row else None
 
    @staticmethod
    def deactivate_account(aid: int, actor_id: int, actor_email: str) -> Optional[AccountResponse]:
        """Logs account_deactivated."""
        print(f"[AUTH] Admin clearance confirmed for deactivation (POC stub) — actor aid={actor_id}, target aid={aid}")
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE accounts SET is_active = FALSE, updated_at = NOW()
                WHERE aid = %s
                RETURNING aid, name, email, clearance, is_active, created_at, updated_at
                """,
                (aid,),
            )
            row = cursor.fetchone()
            if row:
                _write_audit_log(cursor, "account_deactivated", actor_id=actor_id,actor_email=actor_email, target_id=aid, target_email=row[2])
            conn.commit()
        return _row_to_account(row) if row else None
 
    @staticmethod
    def list_audit_log(event_type=None, date_from=None, date_to=None) -> List[AuditLogEntry]:
        clauses, values = [], []
        if event_type:
            clauses.append("event_type = %s"); values.append(event_type)
        if date_from:
            clauses.append("created_at >= %s"); values.append(date_from)
        if date_to:
            clauses.append("created_at <= %s"); values.append(date_to)
 
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, event_type, actor_id, actor_email, target_id, target_email, detail, created_at FROM audit_log {where} ORDER BY created_at DESC",values)
            rows = cursor.fetchall()
        return [
            AuditLogEntry(id=r[0], event_type=r[1], actor_id=r[2], actor_email=r[3],target_id=r[4], target_email=r[5], detail=r[6], created_at=r[7])
            for r in rows
        ]