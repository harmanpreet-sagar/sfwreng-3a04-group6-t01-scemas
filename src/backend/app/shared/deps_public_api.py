"""
FastAPI dependency: validate public API keys from the Authorization header.

Separate from operator/admin JWT auth.

- `PublicApiKeyDep` — key validation only.
- `PublicApiKeyRateLimitedDep` — validation plus 100 req/min per key (in-memory).
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException
from starlette.requests import Request

from app.models.public_api_key import PublicApiKeyAuth
from app.services.api_key_repository import fetch_active_api_key_by_hash
from app.shared.api_key_hash import api_key_sha256_hex
from app.shared.db import get_supabase_db_url
from app.shared.public_api_errors import public_api_error_payload
from app.shared.public_api_rate_limiter import public_api_rate_limiter


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if authorization is None or not authorization.strip():
        raise HTTPException(
            status_code=401,
            detail=public_api_error_payload(
                error="api_key_missing",
                message="Missing Authorization header with a valid API key.",
            ),
        )
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail=public_api_error_payload(
                error="api_key_invalid",
                message=(
                    "Authorization must use the Bearer scheme: "
                    "'Authorization: Bearer <api_key>'."
                ),
            ),
        )
    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail=public_api_error_payload(
                error="api_key_invalid",
                message=(
                    "Authorization must use the Bearer scheme: "
                    "'Authorization: Bearer <api_key>'."
                ),
            ),
        )
    return token


def require_public_api_key(
    request: Request,
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
) -> PublicApiKeyAuth:
    if not get_supabase_db_url():
        raise HTTPException(
            status_code=503,
            detail=public_api_error_payload(
                error="service_unavailable",
                message="Database is not configured (SUPABASE_DB_URL).",
            ),
        )
    plaintext = _extract_bearer_token(authorization)
    digest = api_key_sha256_hex(plaintext)
    row = fetch_active_api_key_by_hash(digest)
    if row is None:
        raise HTTPException(
            status_code=401,
            detail=public_api_error_payload(
                error="api_key_invalid",
                message="The API key is invalid or inactive.",
            ),
        )
    auth = PublicApiKeyAuth(id=row["id"], label=row["label"])
    request.state.public_api_key_id = auth.id
    request.state.public_api_key_label = auth.label
    return auth


PublicApiKeyDep = Annotated[PublicApiKeyAuth, Depends(require_public_api_key)]


def enforce_public_api_rate_limit(
    api_key: PublicApiKeyDep,
) -> PublicApiKeyAuth:
    """
    Compose after API key validation: 100 req/min per key (in-memory sliding window).

    Use `PublicApiKeyRateLimitedDep` on public routes that should be throttled.
    """
    denied = public_api_rate_limiter.try_acquire(api_key.id)
    if denied is not None:
        raise HTTPException(
            status_code=429,
            detail=public_api_error_payload(
                error="rate_limit_exceeded",
                message="Too many requests for this API key. Try again later.",
                key_id=api_key.id,
                limit=denied.limit,
                window_seconds=denied.window_seconds,
                retry_after_seconds=denied.retry_after_seconds,
            ),
            headers={"Retry-After": str(denied.retry_after_seconds)},
        )
    return api_key


PublicApiKeyRateLimitedDep = Annotated[
    PublicApiKeyAuth, Depends(enforce_public_api_rate_limit)
]
