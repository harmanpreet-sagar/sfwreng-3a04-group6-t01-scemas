"""
Minimal public route to smoke-test API key auth (PoC).

Real public endpoints can use the same dependency from app.shared.deps_public_api.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.shared.deps_public_api import PublicApiKeyRateLimitedDep

router = APIRouter(prefix="/api/public", tags=["Public API"])


@router.get("/whoami")
def public_whoami(api_key: PublicApiKeyRateLimitedDep) -> dict:
    """Returns validated key metadata (for curl / integration checks only)."""
    return {"key_id": api_key.id, "label": api_key.label}
