"""
Proof-of-concept auth helpers for the accounts router.

The router imports get_current_account and require_admin from here. Identity is
read from request headers instead of a JWT so flows can be tested without a full
auth stack. Prefer shared/auth.py (JWT + require_admin) for production routes.

Headers:
    X-Account-Id        — numeric account aid
    X-Account-Clearance — "admin" | "operator"
    X-Account-Email     — optional; used in audit logs
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException


def get_current_account(
    x_account_id: int = Header(..., description="PoC: your account aid"),
    x_account_clearance: str = Header(..., description="PoC: 'admin' or 'operator'"),
    x_account_email: str = Header("unknown@demo.com"),
) -> dict:
    """Return caller identity extracted from PoC stub headers."""
    print(f"[AUTH] Identity verified (POC stub) — aid={x_account_id}, clearance={x_account_clearance}")
    return {
        "aid": x_account_id,
        "clearance": x_account_clearance,
        "email": x_account_email,
    }


def require_admin(current: dict = Depends(get_current_account)) -> dict:
    """
    Reject non-admin callers with 403.

    Can be swapped for shared/auth.require_admin once all routes use JWT claims.
    """
    if current["clearance"] != "admin":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Admin clearance required.",
                "your_clearance": current["clearance"],
            },
        )
    print(f"[AUTH] Admin clearance confirmed (POC stub) — aid={current['aid']}")
    return current
