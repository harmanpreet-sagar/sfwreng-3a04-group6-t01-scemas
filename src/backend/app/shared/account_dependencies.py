"""
PoC authentication stub for the Account Management subsystem (Jason).

Jason's accounts router imports get_current_account and require_admin from
here.  This file is shared infrastructure — it lives in our branch so the
import resolves the moment Jason's router PR is merged.

Identity is read from plain request headers instead of a JWT so the accounts
router can be exercised without a running auth server.  Once Jason's login
endpoint is integrated with shared/auth.py (which issues real JWTs), this
file can be replaced with wrappers around require_admin / _extract_user.

Headers consumed by Jason's router:
    X-Account-Id        — numeric account aid
    X-Account-Clearance — "admin" | "operator"
    X-Account-Email     — (optional) actor e-mail recorded in audit logs
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException


def get_current_account(
    x_account_id: int = Header(..., description="PoC: your account aid"),
    x_account_clearance: str = Header(..., description="PoC: 'admin' or 'operator'"),
    x_account_email: str = Header("unknown@demo.com"),
) -> dict:
    """Return caller identity extracted from PoC stub headers."""
    return {
        "aid": x_account_id,
        "clearance": x_account_clearance,
        "email": x_account_email,
    }


def require_admin(current: dict = Depends(get_current_account)) -> dict:
    """
    Reject non-admin callers with 403.

    Will be replaced by a wrapper around shared/auth.py's require_admin()
    once JWT tokens carry a clearance/role claim from Jason's login endpoint.
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
    return current
