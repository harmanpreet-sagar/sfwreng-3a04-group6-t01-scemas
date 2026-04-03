"""
POC Auth stub, replaces actual authentication
 
Accepts a plain account ID in the
X-Account-Id header and a clearance level in X-Account-Clearance, auto-trusting them
"""
 
from __future__ import annotations
 
from fastapi import Depends, Header, HTTPException
 
 
def get_current_account(
    x_account_id: int = Header(..., description="POC: pass your account aid here"),
    x_account_clearance: str = Header(..., description="POC: pass 'admin' or 'operator'"),
    x_account_email: str = Header("unknown@demo.com"),
) -> dict:
    """
    POC identity check, stub for demonstration
    """
    print(f"[AUTH] Identity verified (POC stub) — aid={x_account_id}, clearance={x_account_clearance}")
    return {
        "aid":       x_account_id,
        "clearance": x_account_clearance,
        "email":     x_account_email,
    }
 
 
def require_admin(current: dict = Depends(get_current_account)) -> dict:
    """
    POC clearance check, for a full application would abide by RBAC rules
    For now: clearance level accepted as declared.
    """
    if current["clearance"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="[POC] Admin clearance required. In production, this would be enforced via RBAC.",
        )
    print(f"[AUTH] Admin clearance confirmed (POC stub) — aid={current['aid']}")
    return current