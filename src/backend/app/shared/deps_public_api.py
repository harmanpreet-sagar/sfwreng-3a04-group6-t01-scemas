"""
FastAPI dependency: validate public API keys from the Authorization header.

Separate from operator/admin JWT auth. Use `Depends(require_public_api_key)` on public routes.
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException

from app.models.public_api_key import PublicApiKeyAuth
from app.services.api_key_repository import fetch_active_api_key_by_hash
from app.shared.api_key_hash import api_key_sha256_hex


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if authorization is None or not authorization.strip():
        raise HTTPException(
            status_code=401,
            detail={
                "error": "api_key_missing",
                "message": "Missing Authorization header with a valid API key.",
            },
        )
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={
                "error": "api_key_invalid",
                "message": (
                    "Authorization must use the Bearer scheme: "
                    "'Authorization: Bearer <api_key>'."
                ),
            },
        )
    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "api_key_invalid",
                "message": (
                    "Authorization must use the Bearer scheme: "
                    "'Authorization: Bearer <api_key>'."
                ),
            },
        )
    return token


def require_public_api_key(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
) -> PublicApiKeyAuth:
    plaintext = _extract_bearer_token(authorization)
    digest = api_key_sha256_hex(plaintext)
    row = fetch_active_api_key_by_hash(digest)
    if row is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "api_key_invalid",
                "message": "The API key is invalid or inactive.",
            },
        )
    return PublicApiKeyAuth(id=row["id"], label=row["label"])


PublicApiKeyDep = Annotated[PublicApiKeyAuth, Depends(require_public_api_key)]
